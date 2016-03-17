from views_common import *
from django.utils.translation import ugettext_lazy as _

from participant_key_filter import participant_key_filter
from ReadWriteTag import ReadTag, WriteTag

#--------------------------------------------------------------------------
@autostrip
class SelfServeAntennaForm( Form ):
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label = _('Configure the RFID Antenna to Read Tags') )
	
	def __init__(self, *args, **kwargs):
		super(SelfServeAntennaForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('rfid_antenna'), ),
			Row( button_args[0], ),
		)
		
@access_validation( True )
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
		# Find the next competition by date.
		competition = Competition.objects.filter(start_date__gte=datetime.date.today()).order_by('-start_date').first()
		# If that fails, just get the latest competition for testing.
		if not competition:
			competition = Competition.objects.all().order_by('-start_date').first()
		if not competition:
			errors.append( _('No Competition Found') )
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
		
	if not participants:
		errors.append( _('Not Registered') )

	license_holder_errors = (
		('good_waiver',			_('Missing/Expired Insurance Waiver')),
	)
	license_holder_warnings = (
		('good_license',		_('Temporary License (do you have a permanent one now?)')),
		('good_uci_code',		_('Incorrect UCI Code')),
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
