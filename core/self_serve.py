from django.utils.translation import gettext_lazy as _

from .views_common import *
from .participant_key_filter import participant_key_filter, add_participant_from_license_holder
from .ReadWriteTag import ReadTag, WriteTag
from .participant import ParticipantSignatureForm
from .get_version import get_version

def get_valid_competitions():
	dNow = timezone.localtime(timezone.now()).date()
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
				choices = lambda: [(c.pk, format_lazy('{} - {}', c.name, c.date_range_str))
					for c in get_valid_competitions()],
				label = _('Choose a Competition') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', '' ),	# Styling by template.
		]
		
		self.helper.layout = Layout(
			Row( Field('competition_choice', size=8, style="font-size: 250%;"), ),
			Row( button_args[0], ),
		)
		
@autostrip
class SelfServeAntennaForm( Form ):
	rfid_antenna = forms.ChoiceField( choices = [(-1, _("USB Reader"))] + [(i, mark_safe('&nbsp;&nbsp;&nbsp;Ant {}&nbsp;&nbsp;&nbsp;'.format(i))) for i in range(1,5)], label = _('Antenna to Read Tags') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', '' ),	# Styled by template.
		]
		
		self.helper.layout = Layout(
			Row( Field('rfid_antenna', size=5, style="font-size: 250%;"), ),
			Row( button_args[0], ),
		)

@autostrip
class SelfServeUSBReader( Form ):
	rfid_tag = forms.CharField( label=_('RFID Tag') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', '' ),	# Styled by the template.
		]
		
		self.helper.layout = Layout(
			Row( Field('rfid_tag', size=40), ),
			Row( HTML('<hr/>') ),
			Row( button_args[0], ),
		)

@access_validation( selfserve_ok=True )
def SelfServeQRCode( request ):
	# Prevent non-serve users from coming here.
	if request.user.username != 'serve':
		return HttpResponseRedirect( '/RaceDB' )
	
	exclude_breadcrumbs = True
	qrpath = request.build_absolute_uri()
	
	for i in range(2):
		qrpath = os.path.dirname( qrpath )
	qrpath += '/login/?next=/RaceDB/SelfServe/'

	qrcode_note = _('Login with Username: serve')
	return render( request, 'qrcode.html', locals() )

@access_validation( selfserve_ok=True )
def SelfServeSignature( request ):
	url_error = getContext(request, 'popUrl') + '/SelfServe/'
	competition_id = request.session.get('competition_id', None)
	if not competition_id:
		return HttpResponseRedirect( url_error )
	competition = get_object_or_404( Competition, pk=competition_id )
	
	tag = request.session.get('tag', None)
	if not tag:
		return HttpResponseRedirect( url_error )
	
	license_holder, participants = participant_key_filter( competition, tag, False )
	if not license_holder or not participants:
		return HttpResponseRedirect( url_error )
	
	participant = participants[0]
	if request.method == 'POST':
		form = ParticipantSignatureForm( request.POST )
		if form.is_valid():
			signature = form.cleaned_data['signature']
			if not signature:
				return HttpResponseRedirect( url_error )
			
			for p in participants:
				p.signature = signature				
			Participant.objects.bulk_update( participants, 'signature' )
			
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantSignatureForm()
		
	return render( request, 'self_serve_signature.html', dict(
			request=request,
			url_error=url_error,
			form=form,
			participant=participant,
			competition=competition
		)
	)

#----------------------------------------------------------------------------
# action states:
# 0: show self serve screen
# 1: read rfid
# 2: confirm logout
# 3: do logout
# 4: get signature
	
@access_validation( selfserve_ok=True )
def SelfServe( request, action=0 ):
	# Prevent non-serve users from coming here.
	if request.user.username != 'serve':
		return HttpResponseRedirect( '/RaceDB' )
	
	action = int(action)
	
	exclude_breadcrumbs = True
	version = get_version()
	
	form = None
	status_entries = []
	errors = []
	warnings = []
	license_holder = None
	participants = []
	confirm_logout = False
	
	path_noargs = getContext(request, 'cancelUrl') + 'SelfServe/'
	
	if action != 4:
		# Forget rfid_tag if not retrieve signature.
		request.session['rfid_tag'] = None
	
	if action == 2:
		confirm_logout = True
		return render( request, 'self_serve.html', locals() )
	elif action == 3:
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

	# If there is no rfid reader available, default to a usb reader.
	if not competition.has_rfid_reader():
		rfid_antenna = request.session['rfid_antenna'] = -1
		action = 1
	else:
		rfid_antenna = request.session.get('rfid_antenna', None)
		
	# Othewise, get the rfid reader antenna to use.
	if action == 0 or rfid_antenna is None:
		
		if request.method == 'POST':
			form = SelfServeAntennaForm( request.POST )
			if form.is_valid():
				rfid_antenna = int(form.cleaned_data['rfid_antenna'])
				if not rfid_antenna:
					return HttpResponseRedirect( path_noargs )
				request.session['rfid_antenna'] = rfid_antenna
			return HttpResponseRedirect( path_noargs + '1/' )
		else:
			form = SelfServeAntennaForm()
			return render( request, 'self_serve.html', locals() )

	# Read the tag.
	debugRFID = False
	if rfid_antenna == -1:
		# Get the value from the USB Reader.
		if request.method == 'POST':
			form = SelfServeUSBReader( request.POST )
			if form.is_valid():
				rfid_tag = form.cleaned_data['rfid_tag']
				tags = [rfid_tag]
				status = True
				form = None
			else:
				return render( request, 'self_serve.html', locals() )
		else:
			form = SelfServeUSBReader()
			return render( request, 'self_serve.html', locals() )
	else:
		# Scan from a RFID Reader antenna.
		rfid_tag = request.session.get('rfid_tag', None)
		if rfid_tag:
			tags = [rfid_tag]
			status = True
		else:
			if not debugRFID:
				rfid_tag = None
				status, response = ReadTag(rfid_antenna)
				if not status:
					status_entries.append(
						(_('Tag Read Failure'), response.get('errors',[]) ),
					)
				else:
					tags = response.get('tags', [])
					try:
						rfid_t = tags[0]
					except (AttributeError, IndexError) as e:
						status = False
						status_entries.append(
							(_('Tag Read Failure'), [e] ),
						)
			else:
				rfid_tag = '8F7200647614'
				tags = [rfid_tag]
				status = True
		
	if rfid_tag and len(tags) > 1:
		status = False
		tags = [add_name_to_tag(competition, t) for t in tags]
		if len(tags) > 4:
			tags = tags[:4] + ['...']
		status_entries.append(
			(_('Multiple Tags Read (ensure only ONE tag is near the antenna).'), tags )
		)

	if not status:
		return render( request, 'self_serve.html', locals() )
	
	request.session['rfid_tag'] = rfid_tag
	license_holder, participants = participant_key_filter( competition, rfid_tag, False )
	
	if not license_holder:
		request.session['rfid_tag'] = None
		errors.append( format_lazy('{} ({}).', _('Tag not found'), rfid_tag) )
		return render( request, 'self_serve.html', locals() )
	
	# If the license holder has a season's pass for the competition, try to add him/her as a participant.
	if not participants and competition.seasons_pass:
		if competition.seasons_pass.has_license_holder(license_holder):
			license_holder, participants = add_participant_from_license_holder( competition, license_holder )
		else:
			errors.append( _("Season's Pass required.") )
	
	if not participants:
		errors.append( _('Not Registered') )
	else:
		bulk_update_if_different( Participant, participants, 'tag_checked', True )	
		
	if not errors and competition.show_signature:
		if not all( p.good_signature() for p in participants ):
			return HttpResponseRedirect( getContext(request, 'cancelUrl') + 'SelfServe/4/SelfServeSignature/' )
		
	if not errors:
		errors, warnings = participants[0].get_lh_errors_warnings()
		for p in participants:
			e, w = p.get_errors_warnings()
			errors.extend( e )
			warnings.extend( w )
				
	if not errors:
		bulk_update_if_different( Participant, participants, 'confirmed', True )

	return render( request, 'self_serve.html', locals() )
