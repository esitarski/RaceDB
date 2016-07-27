from views_common import *
from django.utils.translation import ugettext_lazy as _

from participant_key_filter import participant_key_filter, add_participant_from_license_holder
from ReadWriteTag import ReadTag, WriteTag

#--------------------------------------------------------------------------
@autostrip
class SelfServeCompetitionForm( Form ):
	competition_choice = forms.ChoiceField(
				choices = lambda: [(c.pk, string_concat(c.name, ' - ', c.date_range_str))
					for c in Competition.objects.filter(start_date__gte=datetime.date.today()).order_by('start_date')],
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
	return render_to_response( 'qrcode.html', RequestContext(request, locals()) )
	
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
		return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
	elif do_scan == 3:
		logout( request )
		return HttpResponseRedirect( '/RaceDB/Home/' )		
		
	competition_id = request.session.get('competition_id', None)
	competition = Competition.objects.filter( pk=competition_id ).first() if competition_id else None
	
	if competition is None:
		# Find the self-serve competition.
		competitions = list(Competition.objects.filter(start_date__gte=datetime.date.today()).order_by('start_date'))
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
					return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
			else:
				form = SelfServeCompetitionForm()
				return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
		
		if not competition:
			errors.append( _('No Competition') )
			return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
		
		request.session['competition_id'] = competition_id = competition.id
		
	if not competition.using_tags:
		errors.append( _('Competition must be configured to use tags.') )
		return render_to_response( 'self_serve.html', RequestContext(request, locals()) )

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
			return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
		
	if not do_scan:
		return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
	
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
	
	if tag and len(tags) > 1:
		status = False
		if len(tags) > 4:
			tags = tags[:4] + ['...']
		status_entries.append(
			(_('Multiple Tags Read (check that only one tag is near the antenna).'), [u', '.join(tags)] )
		)

	if not status:
		return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
		
	license_holder, participants = participant_key_filter( competition, tag, False )
	
	if not license_holder:
		errors.append( string_concat(_('Tag not found '), u' (', tag, u').') )
		return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
	
	# If the license holder has a season's pass for the competition, try to add him/her as a participant.
	if not participants and competition.seasons_pass and competition.seasons_pass.has_license_holder(license_holder):
		license_holder, participants = add_participant_from_license_holder( competition, license_holder )
		
	if not participants:
		errors.append( _('Not Registered') )

	license_holder_errors = (
		('good_eligible',		_('Ineligible to Compete')),
		('good_waiver',			_('Missing/Expired Insurance Waiver')),
	)
	license_holder_warnings = (
		('good_license',			_('Temporary License (do you have a permanent one now?)')),
		('good_uci_code',			_('Incorrect UCI Code')),
		('good_emergency_contact',	_('Incomplete Emergency Contact')),
	)
	
	participant_errors = (
		('good_paid',			_('Missing Payment')),
		('good_bib',			_('Missing Bib Number')),
		('good_category',		_('Missing Category')),
		('good_tag',			_('Missing Tag')),
		('good_signature',		_('Missing Signature')),
	)
	participant_warnings = (
		#('good_team',			_('No Team Name on File')),
		('good_est_kmh',		_('Missing Estimated TT Speed')),
	)
	for i, p in enumerate(participants):
		if i == 0:
			for check, message in license_holder_errors:
				if not getattr(p, check)():
					errors.append( message )
			for check, message in license_holder_warnings:
				if not getattr(p, check)():
					warnings.append( message )
		
		for check, message in participant_warnings:
			if not getattr(p, check)():
				warnings.append( message )
		for check, message in participant_errors:
			if not getattr(p, check)():
				if check in ('good_bib', 'good_paid'):
					errors.append( string_concat(message, u' (', p.category.code if p.category else _('Missing Category'),u')') )
				else:
					errors.append( message )
				
	if not errors:
		for p in participants:
			p.confirmed = True
			p.save()

	return render_to_response( 'self_serve.html', RequestContext(request, locals()) )
