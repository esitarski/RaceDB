from views_common import *
import operator

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from participant_key_filter import participant_key_filter, add_participant_from_license_holder
from ReadWriteTag import ReadTag, WriteTag

def get_valid_competitions():
	dNow = timezone.now().date()
	return [
		c for c in Competition.objects.filter(
			start_date__gte=dNow-datetime.timedelta(days=365)).order_by(
			'start_date')
		if c.start_date + datetime.timedelta(days=(c.number_of_days or 1)) > dNow
	]

#--------------------------------------------------------------------------
@autostrip
class SelfServeCompetitionForm( Form ):
	competition_choice = forms.ChoiceField(
				choices = lambda: [(c.pk, string_concat(c.name, ' - ', c.date_range_str))
					for c in get_valid_competitions()],
				label = _('Choose a Competition') )
	
	def __init__(self, *args, **kwargs):
		super(SelfServeCompetitionForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('competition_choice', size=8, style="font-size: 250%;"), ),
			Row( button_args[0], ),
		)
		
@autostrip
class SelfServeAntennaForm( Form ):
	rfid_antenna = forms.ChoiceField( choices = [(i, mark_safe('&nbsp;&nbsp;&nbsp;{}&nbsp;&nbsp;&nbsp;'.format(i))) for i in xrange(1,5)], label = _('Antenna to Read Tags') )
	
	def __init__(self, *args, **kwargs):
		super(SelfServeAntennaForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('rfid_antenna', size=4, style="font-size: 250%;"), ),
			Row( button_args[0], ),
		)

@access_validation( selfserve_ok=True )
def SelfServeQRCode( request ):
	# Prevent non-serve users from coming here.
	if request.user.username != 'serve':
		return HttpResponseRedirect( '/RaceDB' )
	
	exclude_breadcrumbs = True
	qrpath = request.build_absolute_uri()
	
	for i in xrange(2):
		qrpath = os.path.dirname( qrpath )
	qrpath += '/login/?next=/RaceDB/SelfServe/'

	qrcode_note = _('Login with Username: serve')
	return render( request, 'qrcode.html', locals() )
	
@access_validation( selfserve_ok=True )
def SelfServe( request, do_scan=0 ):
	# Prevent non-serve users from coming here.
	if request.user.username != 'serve':
		return HttpResponseRedirect( '/RaceDB' )
	
	do_scan = int(do_scan)
	
	exclude_breadcrumbs = True
	version = RaceDBVersion
	
	form = None
	status_entries = []
	errors = []
	warnings = []
	license_holder = None
	participants = []
	confirm_logout = False
	
	path_noargs = getContext(request, 'cancelUrl') + 'SelfServe/'
	
	if do_scan == 2:
		confirm_logout = True
		return render( request, 'self_serve.html', locals() )
	elif do_scan == 3:
		logout( request )
		return HttpResponseRedirect( '/RaceDB/Home/' )		
		
	competition_id = request.session.get('competition_id', None)
	competition = Competition.objects.filter( pk=competition_id ).first() if competition_id else None
	
	if competition is None:
		competitions = get_valid_competitions()
		if not competitions:
			# Get the latest competition for testing.
			competition = Competition.objects.all().order_by('-start_date').first()
		elif len(competitions) == 1:
			competition = competitions[0]
		else:
			# Ask the user what competition they want.
			if request.method == 'POST':
				form = SelfServeCompetitionForm( request.POST )
				if form.is_valid():
					competition = Competition.objects.filter( pk=form.cleaned_data['competition_choice'] ).first()
				else:
					return render( request, 'self_serve.html', locals() )
			else:
				form = SelfServeCompetitionForm()
				return render( request, 'self_serve.html', locals() )
		
		if not competition:
			errors.append( _('No Competition') )
			return render( request, 'self_serve.html', locals() )
		
		request.session['competition_id'] = competition_id = competition.id
		
	if not competition.using_tags:
		errors.append( _('Competition must be configured to use tags.') )
		return render( request, 'self_serve.html', locals() )

	rfid_antenna = request.session.get('rfid_antenna', None)
	if rfid_antenna is None:
		if request.method == 'POST':
			form = SelfServeAntennaForm( request.POST )
			if form.is_valid():
				rfid_antenna = int(form.cleaned_data['rfid_antenna'])
				if not rfid_antenna:
					return HttpResponseRedirect( path_noargs )
				request.session['rfid_antenna'] = rfid_antenna
			
			return HttpResponseRedirect( path_noargs )
		else:
			form = SelfServeAntennaForm()
			return render( request, 'self_serve.html', locals() )
		
	if not do_scan:
		return render( request, 'self_serve.html', locals() )

	debug = True
	if not debug:
		tag = None
		status, response = ReadTag(rfid_antenna)
		if not status:
			status_entries.append(
				(_('Tag Read Failure'), response.get('errors',[]) ),
			)
		else:
			tags = response.get('tags', [])
			try:
				tag = tags[0]
			except (AttributeError, IndexError) as e:
				status = False
				status_entries.append(
					(_('Tag Read Failure'), [e] ),
				)
	else:
		tag = '8F7200647614'
		tags = [tag]
		status = True
	
	if tag and len(tags) > 1:
		status = False
		if len(tags) > 4:
			tags = tags[:4] + ['...']
		status_entries.append(
			(_('Multiple Tags Read (check that only one tag is near the antenna).'), [u', '.join(tags)] )
		)

	if not status:
		return render( request, 'self_serve.html', locals() )
	
	license_holder, participants = participant_key_filter( competition, tag, False )
	
	if not license_holder:
		errors.append( string_concat(_('Tag not found '), u' (', tag, u').') )
		return render( request, 'self_serve.html', locals() )
	
	# If the license holder has a season's pass for the competition, try to add him/her as a participant.
	if not participants and competition.seasons_pass and competition.seasons_pass.has_license_holder(license_holder):
		license_holder, participants = add_participant_from_license_holder( competition, license_holder )
		
	if not participants:
		errors.append( _('Not Registered') )
		
	errors, warnings = participants[0].get_lh_errors_warnings()
	for p in participants:
		e, w = p.get_errors_warnings()
		errors.extend( e )
		warnings.extend( w )
				
	if not errors:
		for p in participants:
			p.confirmed = True
			p.save()

	return render( request, 'self_serve.html', locals() )
