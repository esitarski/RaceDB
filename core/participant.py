from views_common import *
import uuid
from subprocess import Popen, PIPE
from get_id import get_id
import traceback

from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from views import BarcodeScanForm, RfidScanForm

from print_bib import print_bib_tag_label, print_id_label, print_body_bib, print_shoulder_bib

from participant_key_filter import participant_key_filter, participant_bib_filter

from get_participant_excel import get_participant_excel
from emails import show_emails
from gs_cmd import gs_cmd

from ReadWriteTag import ReadTag, WriteTag

def get_participant( participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	return participant.enforce_tag_constraints()

@autostrip
class ParticipantSearchForm( Form ):
	scan = forms.CharField( required=False, label = _('Scan Search'), help_text=_('Searches License and RFID Tag only') )
	event = forms.ChoiceField( required=False, label = _('Event'), help_text=_('For faster response, review one Event at a time') )
	name_text = forms.CharField( required=False, label = _('Name Text') )
	team_text = forms.CharField( required=False, label = _('Team Text') )
	bib = forms.IntegerField( required=False, min_value = -1 , label=_('Bib: (-1 for Missing)') )
	rfid_text = forms.CharField( required=False, label = _('RFIDTag: (-1 for Missing)') )
	gender = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('Men')), (1, _('Women'))), initial = 2 )
	role_type = forms.ChoiceField( required=False, label = _('Role Type')  )
	category = forms.ChoiceField( required=False, label = _('Category') )
	
	city_text = forms.CharField( required=False, label = _('City') )
	state_prov_text = forms.CharField( required=False, label = _('State/Prov') )
	nationality_text = forms.CharField( required=False, label = _('Nationality') )
	
	confirmed = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Confirmed') )
	paid = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Paid') )
	
	complete = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Complete') )
	
	has_events = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('None')), (1, _('Some'))), label = _('Has Events') )
	
	eligible = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Eligible') )
	
	def __init__(self, *args, **kwargs):
		competition = kwargs.pop( 'competition', None )
		super(ParticipantSearchForm, self).__init__(*args, **kwargs)
		
		if competition:
			self.fields['category'].choices = \
				[(-1, '----')] + [(-2, _('*** Missing ***'))] + [(category.id, category.code_gender) for category in competition.get_categories()]
			events = sorted( competition.get_events(), key = operator.attrgetter('date_time') )
			self.fields['event'].choices = \
				[(u'-1.0', _('All'))] + [(u'{}.{}'.format(event.event_type, event.id), u'{} {}'.format(event.short_name, timezone.localtime(event.date_time).strftime('%Y-%m-%d %H:%M:%S'))) for event in events]
			
		roleChoices = [(i, role) for i, role in enumerate(Participant.ROLE_NAMES)]
		roleChoices[0] = (0, '----')
		self.fields['role_type'].choices = roleChoices
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'clear-submit', _('Clear Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('OK'), css_class = 'btn btn-primary' ),
			Submit( 'emails-submit', _('Emails'), css_class = 'btn btn-primary' ),
			Submit( 'export-excel-submit', _('Export to Excel'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('scan', size=20, autofocus=True ), HTML('&nbsp;'*8), Field('event'),),
			Row( *(
					[Field('name_text'), Field('team_text'), Field('category'), Field('bib'),] +
					([Field('rfid_text'),] if competition and competition.using_tags else []) +
					[Field('gender'), Field('role_type'),] +
					[Field('city_text'), Field('state_prov_text'), Field('nationality_text'), Field('confirmed'),] + 
					[Field('paid'), Field('complete'), Field('has_events'), Field('eligible'),]
				)
			),
			Row( *(button_args[:-2] + [HTML('&nbsp;'*8)] + button_args[-2:]) ),
		)

@access_validation()
def Participants( request, competitionId ):
	ParticipantsPerPage = 25
	
	competition = get_object_or_404( Competition, pk=competitionId )
	
	pfKey = 'participant_filter_{}'.format( competitionId )
	pageKey = 'participant_filter_page_{}'.format( competitionId )
	participant_filter = request.session.get(pfKey, {})
	
	def getPaginator( participants ):
		paginator = Paginator( participants, ParticipantsPerPage )
		page = request.GET.get('page',None) or request.session.get(pageKey,None)
		try:
			participants = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			page = 1
			participants = paginator.page(page)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			page = paginator.num_pages
			participants = paginator.page(page)
		request.session[pageKey] = page
		return participants, paginator
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'clear-submit' in request.POST:
			request.session[pfKey] = {}
			request.session[pageKey] = None
			return HttpResponseRedirect(getContext(request,'path'))
			
		form = ParticipantSearchForm( request.POST, competition=competition )
		if form.is_valid():
			participant_filter = form.cleaned_data
			request.session[pfKey] = participant_filter
			
			participant_filter_no_scan = participant_filter.copy()
			participant_filter_no_scan.pop( 'scan' )
			
			request.session[pfKey] = participant_filter_no_scan
			request.session[pageKey] = None
	else:
		form = ParticipantSearchForm( competition = competition, initial = participant_filter )
	
	#-------------------------------------------------------------------
	
	event = None
	try:
		event_type, event_pk = [int(v) for v in participant_filter.get('event', '-1.0').split('.')]
	except:
		event_type, event_pk = None, None
	if event_type == 0:
		event = competition.eventmassstart_set.filter(pk=event_pk).first()
	elif event_type == 1:
		event = competition.eventtt_set.filter(pk=event_pk).first()
			
	participants = event.get_participants() if event else competition.participant_set.all()
	
	competitors = participants.filter( role=Participant.Competitor )
	missing_category_count = competitors.filter( category__isnull=True ).count()
	missing_bib_count = competitors.filter( bib__isnull=True ).count()
	missing_tag_count = 0 if not competition.using_tags else competitors.filter( Q(tag__isnull=True) | Q(tag=u'') ).count()
	
	if participant_filter.get('scan',0):
		name_text = utils.normalizeSearch( participant_filter['scan'] )
		names = name_text.split()
		if names:
			q = Q()
			for n in names:
				q |= Q(license_holder__search_text__contains = n)
			participants = participants.filter( q ).select_related('team', 'license_holder')
			participants, paginator = getPaginator( participants )
			return render( request, 'participant_list.html', locals() )
	
	if participant_filter.get('bib',None) is not None:
		bib = participant_filter['bib']
		if bib <= 0:
			participants = participants.filter( bib__isnull=True )
		else:
			participants = participants.filter( bib=bib )
	
	role_type = int(participant_filter.get('role_type',0))
	if role_type > 0:
		participants = participants.filter( role__range=(100*role_type, 100*role_type+99) )
	
	if 0 <= int(participant_filter.get('gender',-1)) <= 1:
		participants = participants.filter( license_holder__gender=participant_filter['gender'])
	
	category_id = int(participant_filter.get('category',-1))
	if category_id > 0:
		participants = participants.filter( category__id=category_id )
	elif category_id == -2:
		participants = participants.filter( category__isnull=True )
		
	if 0 <= int(participant_filter.get('confirmed',-1)) <= 1:
		participants = participants.filter( confirmed=bool(int(participant_filter['confirmed'])) )
	
	if 0 <= int(participant_filter.get('paid',-1)) <= 1:
		participants = participants.filter( paid=bool(int(participant_filter['paid'])) )
	
	if 0 <= int(participant_filter.get('eligible',-1)) <= 1:
		participants = participants.filter( license_holder__eligible=bool(int(participant_filter['eligible'])) )
	
	participants = participants.select_related('team', 'license_holder')
	
	object_checks = []

	if participant_filter.get('name_text','').strip():
		name_text = utils.normalizeSearch( participant_filter['name_text'] )
		names = name_text.split()
		if names:
			for n in names:
				participants = participants.filter( license_holder__search_text__contains=n )
			def name_filter( p ):
				lh_name = utils.removeDiacritic(p.license_holder.full_name()).lower()
				return all(n in lh_name for n in names)
			object_checks.append( name_filter )

	# Create a search function so we get a closure for the search text in the iterator.
	def search_license_holder( search_text, field ):
		search_fields = utils.normalizeSearch( search_text ).split()
		if search_fields:
			object_checks.append( lambda p: utils.matchSearchFields(search_fields, getattr(p.license_holder, field)) )
		
	for field in ('city', 'state_prov', 'nationality'):
		search_field = field + '_text'
		if participant_filter.get(search_field,'').strip():
			search_license_holder(
				participant_filter[search_field],
				field
			)
	
	team_search = participant_filter.get('team_text','').strip()
	if team_search:
		participants = participants.filter( team__isnull = False )
		q = Q()
		for t in team_search.split():
			q &= Q( team__search_text__contains=t )
		participants = participants.filter( q )
		
	if 0 <= int(participant_filter.get('complete',-1) or 0) <= 1:
		complete = bool(int(participant_filter['complete']))
		if complete:
			participants = participants.filter( Participant.get_can_start_query(competition) )
		else:
			participants = participants.exclude( Participant.get_can_start_query(competition) )
		object_checks.append( lambda p: bool(p.is_done) == complete )
		
	if competition.using_tags and participant_filter.get('rfid_text',''):
		rfid = participant_filter.get('rfid_text','').upper()
		if rfid == u'-1':
			participants = participants.filter( Q(tag__isnull=True) | Q(tag=''))
		else:
			participants = participants.filter( tag=rfid )
	
	has_events = int(participant_filter.get('has_events',-1))
	if has_events == 0:
		participants = participants.filter( role = Participant.Competitor )
		object_checks.append( lambda p: not p.has_any_events() )
	elif has_events == 1:
		object_checks.append( lambda p: p.has_any_events() )
	
	if object_checks:
		failed = [p for p in participants if not all(oc(p) for oc in object_checks)]
		if failed:
			participants = participants.exclude( pk__in=[p.pk for p in failed][:800] )

	if request.method == 'POST':
		if 'export-excel-submit' in request.POST:
			xl = get_participant_excel( Q(pk__in=participants.values_list('pk',flat=True)) )
			response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
			response['Content-Disposition'] = 'attachment; filename=RaceDB-Participants-{}.xlsx'.format(
				datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
			)
			return response
		if 'emails-submit' in request.POST:
			return show_emails( request, participants=participants )
			
	participants, paginator = getPaginator( participants )
	return render( request, 'participant_list.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantsInEvents( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	competition_events = sorted( competition.get_events(), key=lambda e: e.date_time )
	event_participants = {}
	for event in competition_events:
		p = event.get_participants()
		event_participants[event] = p
	
	participants = sorted( set.union(*[p for p in event_participants.itervalues()]), key=lambda p: p.license_holder.search_text )
	
	check_codes = {
		'optional_selected':	u"\u2611",
		'optional_deselected':	u"\u2610",
		'default_selected':		u"\u2713",
		'unavailable':			u"",
	}
	for participant in participants:
		event_status = []
		for event in competition_events:
			if participant in event_participants[event]:
				event_status.append( check_codes['optional_selected' if event.optional else 'default_selected'] )
			elif event.optional:
				event_status.append( check_codes['optional_deselected'] )
			else:
				event_status.append( check_codes['unavailable'] )
		participant.event_status = event_status
	
	return render( request, 'participants_in_events.html', locals() )

@autostrip
class BibScanForm( Form ):
	bib = forms.IntegerField( required = False, label = _('Bib') )
	
	def __init__(self, *args, **kwargs):
		hide_cancel_button = kwargs.pop('hide_cancel_button', None)
		super(BibScanForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		if hide_cancel_button:
			button_args = button_args[:-1]
		
		self.helper.layout = Layout(
			Row(
				Field('bib', size=10),
			),
			Row( *button_args ),
		)

@access_validation()
def ParticipantBibAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	add_by_bib = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = BibScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
			bib = form.cleaned_data['bib']
			if not bib:
				return HttpResponseRedirect(getContext(request,'path'))
				
			license_holders, participants = participant_bib_filter( competition, bib )
			if len(participants) == 1 and len(license_holders) == 0:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit', participants[0].id))
			if len(participants) == 0 and len(license_holders) == 1:
				return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holders[0].id))
				
			return render( request, 'participant_scan_error.html', locals() )			
	else:
		form = BibScanForm( hide_cancel_button=True )
	
	return render( request, 'participant_add_bib.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantManualAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	search_text = request.session.get('participant_new_filter', '')
	btns = [('new-submit', 'New License Holder', 'btn btn-success')]
	add_by_manual = True
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderNew') )
			
		form = SearchForm( btns, request.POST, hide_cancel_button=True )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['participant_new_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text}, hide_cancel_button=True )
	
	search_text = utils.normalizeSearch( search_text )
	q = Q( active = True )
	for term in search_text.split():
		q &= Q(search_text__contains = term)
	license_holders = LicenseHolder.objects.filter(q).order_by('search_text')[:MaxReturn]
	
	# Flag which license_holders are already entered in this competition.
	license_holders_in_competition = set( p.license_holder.id
		for p in Participant.objects.select_related('license_holder').filter(competition=competition) )
	
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	return render( request, 'participant_add_list.html', locals() )

@access_validation()
def ParticipantAddToCompetition( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	
	participant = Participant( competition=competition, license_holder=license_holder, preregistered=False ).init_default_values().auto_confirm()
	
	try:
		# Fails if the license_holder is non-unique.
		participant.save()
		participant.add_to_default_optional_events()
	except IntegrityError as e:
		# Recover silently by going directly to edit screen with the existing participant.
		participant = Participant.objects.filter( competition=competition, license_holder=license_holder ).first()
		
	return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))

@access_validation()
def ParticipantAddToCompetitionDifferentCategory( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder, category__isnull=True ).first()
	if participant:
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder ).first()
	if participant:
		participant.id = None
		participant.category = None
		participant.role = Participant.Competitor
		participant.bib = None
		participant.save()
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	return ParticipantAddToCompetition( request, competitionId, licenseHolderId )

@access_validation()
def ParticipantAddToCompetitionDifferentCategoryConfirm( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	competition_age = competition.competition_age( license_holder )
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder, category__isnull=True ).first()
	if participant:
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	return render( request, 'participant_add_to_category_confirm.html', locals() )

@access_validation()
def ParticipantEdit( request, participantId ):
	participant = get_participant( participantId )
	system_info = SystemInfo.get_singleton()
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	competition_age = participant.competition.competition_age( participant.license_holder )
	is_suspicious_age = not (8 <= competition_age <= 90)
	isEdit = True
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	return render( request, 'participant_form.html', locals() )
	
@access_validation()
def ParticipantEditFromLicenseHolder( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	participant = Participant.objects.filter(competition=competition, license_holder=license_holder).first()
	if not participant:
		return ParticipantAddToCompetition( request, competitionId, licenseHolderId )
	return ParticipantEdit( request, participant.id )
	
@access_validation()
def ParticipantRemove( request, participantId ):
	participant = get_participant( participantId )
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	competition_age = participant.competition.competition_age( participant.license_holder )
	is_suspicious_age = not (8 <= competition_age <= 90)
	isEdit = False
	return render( request, 'participant_form.html', locals() )
	
@access_validation()
def ParticipantDoDelete( request, participantId ):
	participant = get_participant( participantId )
	participant.delete()
	return HttpResponseRedirect( getContext(request,'cancelUrl') )

def get_temp_print_filename( request, bib, ftype ):
	port = request.META['SERVER_PORT']
	rfid_antenna = int(request.session.get('rfid_antenna',0))
	major_delimiter = '_'
	minor_delimiter = '-'
	return os.path.join(
		os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
		'pdfs',
		'{}{}{}'.format(
			major_delimiter.join( '{}{}{}'.format(attr, minor_delimiter, value)
				for attr, value in (('bib',bib), ('port',port), ('antenna',rfid_antenna), ('type',ftype)) ),
			
			major_delimiter, uuid.uuid4().hex
		)
	) + '.pdf'

def get_cmd( cmd ):
	if cmd.strip().startswith('$gswin'):
		return cmd.replace('$gswin', gs_cmd() or 'gs_not_found', 1)
	return cmd
	
def print_pdf( request, participant, pdf_str, print_type ):
	system_info = SystemInfo.get_singleton()
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, print_type )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_str )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_str )
		except Exception as e:
			stdout_info, stderr_info = '', e
		
		try:
			os.remove( tmp_file )
		except:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_str, content_type="application/pdf")
		response['Content-Disposition'] = 'inline'
		return response
	else:
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	
@access_validation()
def ParticipantPrintBodyBib( request, participantId, copies=2, onePage=False ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_body_bib(participant, copies, onePage), 'Body' )
	
@access_validation()
def ParticipantPrintBibLabels( request, participantId ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_bib_tag_label(participant), 'Frame' )
	
@access_validation()
def ParticipantPrintShoulderBib( request, participantId ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_shoulder_bib(participant), 'Shoulder' )
	
@access_validation()
def ParticipantPrintEmergencyContactInfo( request, participantId ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_id_label(participant), 'Emergency' )
	
def ParticipantEmergencyContactInfo( request, participantId ):
	participant = get_participant( participantId )
	license_holder = participant.license_holder
	competition = participant.competition
	team_members = None
	if participant.team:
		team_members_non_competitors_at_competition = LicenseHolder.objects.filter(
			pk__in=Participant.objects.filter(competition=competition,team=participant.team).exclude(
			license_holder=license_holder).exclude(
			role=Participant.Competitor).values_list('license_holder',flat=True).distinct()
		)
		team_members_at_competition = LicenseHolder.objects.filter(
			pk__in=Participant.objects.filter(competition=competition,team=participant.team,role=Participant.Competitor).exclude(
			license_holder=license_holder).values_list('license_holder',flat=True).distinct()
		)
		team_members_other = LicenseHolder.objects.filter(
			pk__in=Participant.objects.filter(
				team=participant.team).exclude(
				competition=competition).exclude(
				license_holder=license_holder).exclude(
				license_holder__in=team_members_at_competition).exclude(
				license_holder__in=team_members_non_competitors_at_competition).values_list('license_holder',flat=True).distinct()
		)
	else:
		team_members_non_competitors_at_competition = LicenseHolder.objects.none()
		team_members_at_competition = LicenseHolder.objects.none()
		team_members_other = LicenseHolder.objects.none()
	return render( request, 'participant_emergency_info.html', locals() )
	
@autostrip
class ParticipantCategorySelectForm( Form ):
	gender = forms.ChoiceField( choices = (
									(-1, _('All')),
									(0, _('Men / Open')),
									(1, _('Women / Open')),
									(2, _('Open')),
								),
								initial = -1 )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantCategorySelectForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			HTML( u'{}:&nbsp;&nbsp;&nbsp;&nbsp;'.format( _("Search") ) ),
			Div( Field('gender', css_class = 'form-control'), css_class = 'form-group' ),
			HTML( u'&nbsp;&nbsp;&nbsp;&nbsp;' ),
			button_args[0],
			button_args[1],
		)

@access_validation()
def ParticipantCategoryChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	competition_age = competition.competition_age( license_holder )
	
	gender = None
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = ParticipantCategorySelectForm( request.POST )
		if form.is_valid():
			gender = int(form.cleaned_data['gender'])
	else:
		gender = license_holder.gender
		form = ParticipantCategorySelectForm( initial = dict(gender=gender) )
	
	categories = Category.objects.filter( format=competition.category_format )
	if gender == None:
		gender = license_holder.gender
	if gender != -1:
		categories = categories.filter( Q(gender=2) | Q(gender=gender) )
	available_categories = set( competition.get_available_categories(license_holder, gender=gender, participant_exclude=participant) )
	
	categories_with_numbers = set()
	for cn in CategoryNumbers.objects.filter( competition=competition ):
		if cn.get_numbers():
			categories_with_numbers |= set( cn.categories.all() )
	
	return render( request, 'participant_category_select.html', locals() )	

@access_validation()
def ParticipantCategorySelect( request, participantId, categoryId ):
	participant = get_participant( participantId )
	competition = participant.competition
	if int(categoryId):
		category = get_object_or_404( Category, pk=categoryId )
	else:
		category = None
	
	categories = set()
	for p in Participant.objects.filter(competition=competition, license_holder=participant.license_holder):
		if p != participant and participant.category:
			categories.add( participant.category )
	if competition.is_category_conflict(categories):
		has_error, conflict_explanation, conflict_participant = True, _('Cannot assign to another Category that already exists in an Event.'), None
		return render( request, 'participant_integrity_error.html', locals() )
	
	category_changed = (participant.category != category)
	participant.category = category
	if category and participant.role != Participant.Competitor:
		participant.role = Participant.Competitor
	
	participant.update_bib_new_category()
	
	try:
		participant.auto_confirm().save()
	except IntegrityError:
		has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
		return render( request, 'participant_integrity_error.html', locals() )

	if category_changed:
		participant.add_to_default_optional_events()
	return HttpResponseRedirect(getContext(request,'pop2Url'))

#-----------------------------------------------------------------------
@access_validation()
def ParticipantRoleChange( request, participantId ):
	participant = get_participant( participantId )
	return render( request, 'participant_role_select.html', locals() )

@access_validation()
def ParticipantRoleSelect( request, participantId, role ):
	participant = get_participant( participantId )
	participant.role = int(role)
	if participant.role != Participant.Competitor:
		participant.bib = None
		participant.category = None
		if participant.role >= 200:			# Remove team for non-team roles.
			participant.team = None
	else:
		participant.init_default_values()
	participant.auto_confirm().save()
	return HttpResponseRedirect(getContext(request,'pop2Url'))
	
#-----------------------------------------------------------------------
@access_validation()
def ParticipantBooleanChange( request, participantId, field ):
	participant = get_participant( participantId )
	setattr( participant, field, not getattr(participant, field) )
	if field != 'confirmed':
		participant.auto_confirm()
	participant.save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
#-----------------------------------------------------------------------
@access_validation()
def ParticipantTeamChange( request, participantId ):
	participant = get_participant( participantId )
	search_text = request.session.get('teams_filter', '')
	btns = [('new-submit', _('New Team'), 'btn btn-success')]
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'TeamNew') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['teams_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
		
	search_text = utils.normalizeSearch(search_text)
	q = Q( active=True )
	for n in search_text.split():
		q &= Q( search_text__contains = n )
	teams = Team.objects.filter(q)[:MaxReturn]
	return render( request, 'participant_team_select.html', locals() )
	
@access_validation()
def ParticipantTeamSelect( request, participantId, teamId ):
	participant = get_participant( participantId )
	if int(teamId):
		team = get_object_or_404( Team, pk=teamId )
	else:
		team = None
	
	if False:
		participant.team = team
		participant.auto_confirm().save()
		return HttpResponseRedirect(getContext(request,'pop2Url'))
	
	return HttpResponseRedirect(getContext(request,'popUrl') + 'ParticipantTeamSelectDiscipline/{}/{}/'.format(participantId,teamId))

@autostrip
class TeamDisciplineForm( Form ):
	disciplines = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple,)
	
	def __init__(self, *args, **kwargs):
		super(TeamDisciplineForm, self).__init__(*args, **kwargs)
		
		self.fields['disciplines'].choices = [(d.id, d.name) for d in Discipline.objects.all()]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = ''
		
		buttons = [
			Submit( 'set-all-submit', _('Same Team for All Disciplines'), css_class = 'btn btn-primary' ),
			Submit( 'set-selected-submit', _('Team for Selected Disciplines Only'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row( buttons[0], HTML('&nbsp;'*8), buttons[2] ),
			Field('disciplines'),
			Row( buttons[1] ),
		)

@access_validation()
def ParticipantTeamSelectDiscipline( request, participantId, teamId ):
	participant = get_participant( participantId )
	competition = participant.competition
	if int(teamId):
		team = get_object_or_404( Team, pk=teamId )
	else:
		team = None
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'pop2Url'))
		
		disciplines = []
		if 'set-all-submit' in request.POST:
			disciplines = list( Discipline.objects.all().values_list('id', flat=True) )
		elif 'set-selected-submit' in request.POST:
			form = TeamDisciplineForm( request.POST )
			if form.is_valid():
				disciplines = form.cleaned_data['disciplines']

		participant.team = team
		participant.auto_confirm().save()
		
		today = timezone.now().date()
		for id in disciplines:
			if team:
				try:
					th = TeamHint.objects.get( discipline__id=id, license_holder=participant.license_holder )
					if th.team_id == team.id:
						continue
					th.team = team
				except TeamHint.DoesNotExist:
					th = TeamHint( license_holder=participant.license_holder, team=team )
					th.discipline_id = id
				th.effective_date = today
				th.save()
			else:
				TeamHint.objects.filter( discipline__id=id, license_holder=participant.license_holder ).delete()
		return HttpResponseRedirect(getContext(request,'pop2Url'))
	else:
		form = TeamDisciplineForm( initial = {'disciplines': [competition.discipline_id]} )
		
	return render( request, 'participant_team_select_discipline.html', locals() )


#-----------------------------------------------------------------------
class Bib( object ):
	def __init__( self, bib, license_holder = None, date_lost=None ):
		self.bib = bib
		self.license_holder = license_holder
		self.full_name = license_holder.full_name() if license_holder else ''
		self.date_lost = date_lost

@access_validation()
def ParticipantBibChange( request, participantId ):
	participant = get_participant( participantId )
	if not participant.category:
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	competition      = participant.competition
	category         = participant.category
	number_set       = competition.number_set
	category_numbers = competition.get_category_numbers( category )
	
	if category_numbers:
		available_numbers = sorted( category_numbers.get_numbers() )
		bib_query = category_numbers.get_bib_query()
		category_numbers_defined = True
	else:
		available_numbers = []
		bib_query = None
		category_numbers_defined = False
	
	allocated_numbers = {}
	lost_bibs = {}
	
	# Find available category numbers.
	
	# First, add all numbers allocated to this event (includes pre-reg).
	if available_numbers:
		participants = Participant.objects.filter( competition=competition ).defer( 'signature' )
		participants = participants.filter( category__in=category_numbers.categories.all() ).filter( bib_query ).order_by()
		participants = participants.select_related('license_holder')
		allocated_numbers = { p.bib: p.license_holder for p in participants }
	
	# If there is a NumberSet, add allocated numbers from there.
	if number_set and available_numbers:
		# Exclude available numbers not allowed in the number set.
		range_events = number_set.get_range_events()
		available_numbers = [bib for bib in available_numbers if number_set.is_bib_valid(bib, range_events)]
		
		# Exclude existing bib numbers of all license holders if using existing bibs.
		# For duplicate license holders, check whether the duplicate has ever raced this category before.
		# We don't know if the existing license holders will show up.
		
		bib_max = number_set.get_bib_max_count_all()
		bib_available_all = number_set.get_bib_available_all( bib_query )
		
		# Get all the bibs of license holders that match the category_numbers of this category.
		current_bibs = defaultdict( set )
		nses = number_set.numbersetentry_set.filter( date_lost__isnull=True ).filter( bib_query )
		nses = nses.select_related('license_holder')
		for nse in nses:
			current_bibs[nse.license_holder].add( nse.bib )
		
		# Handle the case of only one bib in the number set.
		for lh, bibs in current_bibs.iteritems():
			if len(bibs) == 1:
				bib = next(iter(bibs))
				if bib_max.get(bib, 0) == 1:
					allocated_numbers[bib] = lh
					
		# Otherwise, scan past participants to check if a license holder in this category owns the bib.
		pprevious = Participant.objects.filter( competition__number_set=number_set, category__in=category_numbers.categories.all() )
		pprevious = pprevious.filter( bib_query ).defer( 'signature' )
		pprevious = pprevious.exclude( bib__in=list(allocated_numbers.iterkeys())[:200] )
		pprevious = pprevious.order_by('-competition__start_date')
		
		for p in pprevious.exclude(license_holder=participant.license_holder).select_related('license_holder'):
			if p.bib not in allocated_numbers and p.bib in current_bibs[p.license_holder]:
				allocated_numbers[p.bib] = p.license_holder
		
		nses = number_set.numbersetentry_set.exclude( date_lost__isnull=True ).filter( bib_query )
		lost_bibs = { bib:date_lost
			for bib, date_lost in nses.order_by('date_lost').values_list('bib','date_lost')
				if bib_available_all.get(bib,-1) == 0
		}
	else:
		lost_bibs = {}
		
	bibs = [Bib(n, allocated_numbers.get(n, None), lost_bibs.get(n,None)) for n in available_numbers]
	del available_numbers
	del allocated_numbers
	del lost_bibs
	
	if bibs and participant.category:
		participants = Participant.objects.filter(competition=competition, category=participant.category).exclude(bib__isnull=True)
		bib_participants = { p.bib:p for p in participants }
		for b in bibs:
			try:
				b.full_name = bib_participants[b.bib].full_name_team
			except:
				pass
	
	has_existing_number_set_bib = (
		number_set and
		participant.bib == number_set.get_bib( competition, participant.license_holder, participant.category )
	)
	return render( request, 'participant_bib_select.html', locals() )
	
@access_validation()
def ParticipantBibSelect( request, participantId, bib ):
	participant = get_participant( participantId )
	competition = participant.competition
	
	done = HttpResponseRedirect(getContext(request,'pop2Url'))
	showSelectAgain = HttpResponseRedirect(getContext(request,'popUrl'))
	
	bib_save = participant.bib
	bib = int(bib)
	
	if competition.number_set and bib_save is not None:
		def set_lost():
			competition.number_set.set_lost( bib_save, participant.license_holder )
	else:
		def set_lost():
			pass
	
	# No change - nothing to do.
	if bib == bib_save:
		return done
	
	# Bib assigned "No Bib".
	if bib < 0:
		participant.bib = None
		set_lost()
		return done		
	
	# Assign new Bib.
	participant.bib = bib
	
	# Check for conflict in events.
	if participant.category:
		bib_conflicts = participant.get_bib_conflicts()
		if bib_conflicts:
			# If conflict, restore the previous bib and repeat.
			participant.bib = bib_save
			return showSelectAgain

	set_lost()
	
	try:
		participant.auto_confirm().save()
	except IntegrityError as e:
		# Assume the Integrity Error is due to a race condition with the bib number.
		return showSelectAgain
	
	return done

#-----------------------------------------------------------------------
@autostrip
class ParticipantNoteForm( Form ):
	note = forms.CharField( widget = forms.Textarea, required = False, label = _('Note') )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantNoteForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row(
				Field('note', css_class = 'form-control', cols = '60'),
			),
			Row(
				button_args[0],
				button_args[1],
			)
		)
		
@access_validation()
def ParticipantNoteChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantNoteForm( request.POST )
		if form.is_valid():
			note = form.cleaned_data['note']
			participant.note = note
			participant.auto_confirm().save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantNoteForm( initial = dict(note = participant.note) )
		
	return render( request, 'participant_note_change.html', locals() )

@access_validation()
def ParticipantGeneralNoteChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantNoteForm( request.POST )
		if form.is_valid():
			note = form.cleaned_data['note']
			license_holder.note = note
			license_holder.save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantNoteForm( initial = dict(note = license_holder.note) )
		
	return render( request, 'participant_note_change.html', locals() )

#-----------------------------------------------------------------------

def GetParticipantOptionForm( participation_optional_events ):
	choices = [(event.option_id, u'{} ({})'.format(event.name, event.get_event_type_display()))
					for event, is_participating in participation_optional_events]
	
	@autostrip
	class ParticipantOptionForm( Form ):
		options = forms.MultipleChoiceField( required = False, label = _('Optional Events'), choices=choices )
		
		def __init__(self, *args, **kwargs):
			super(ParticipantOptionForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Field('options', css_class = 'form-control', size = '20'),
				),
				Row(
					button_args[0],
					button_args[1],
				)
			)
	
	return ParticipantOptionForm
		
@access_validation()
def ParticipantOptionChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	participation_events = participant.get_participant_events()
	participation_optional_events = [(event, is_participating) for event, optional, is_participating in participation_events if optional]
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = GetParticipantOptionForm( participation_optional_events )( request.POST )
		if form.is_valid():
			options = form.cleaned_data['options']
			ParticipantOption.set_option_ids( participant, options )
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = GetParticipantOptionForm( participation_optional_events )(
			initial = dict(options = [event.option_id for event, is_participating in participation_optional_events if is_participating])
		)
		
	return render( request, 'participant_option_change.html', locals() )
	
#-----------------------------------------------------------------------

def GetParticipantEstSpeedForm( competition ):
	@autostrip
	class ParticipantEstSpeedForm( Form ):
		est_speed = forms.FloatField( required = False,
			label=string_concat(_('Estimated speed for Time Trial'), ' (', competition.speed_unit_display, ')'),
			help_text=_('Enter a value or choose from the grid below.')
		)
		seed_option = forms.ChoiceField( required = False, choices=Participant.SEED_OPTION_CHOICES, label=_('Seed Option'),
			help_text=_('Tells RaceDB to start this rider as Early or as Late as possible in the Start Wave')
		)
		
		def __init__(self, *args, **kwargs):
			super(ParticipantEstSpeedForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Col(Field('est_speed', css_class = 'form-control', size = '20'), 5),
					Col(Field('seed_option'), 6),
				),
				Row(
					button_args[0],
					button_args[1],
				)
			)
	
	return ParticipantEstSpeedForm
		
@access_validation()
def ParticipantEstSpeedChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = GetParticipantEstSpeedForm(competition)( request.POST )
		if form.is_valid():
			est_speed = form.cleaned_data['est_speed']
			participant.est_kmh = competition.to_kmh( est_speed or 0.0 )
			participant.seed_option = form.cleaned_data['seed_option']
			participant.save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = GetParticipantEstSpeedForm(competition)(
			initial = dict( est_speed=competition.to_local_speed(participant.est_kmh), seed_option=participant.seed_option )
		)
	
	speed_rc = {}
	if competition.distance_unit == 0:
		for col, kmh in enumerate(xrange(20, 51)):
			for row, decimal in enumerate(xrange(0, 10)):
				speed_rc[(col, row)] = u'{}.{:01d}'.format(kmh, decimal)
	else:
		for col, mph in enumerate(xrange(12, 32)):
			for row, decimal in enumerate(xrange(0, 10)):
				speed_rc[(col, row)] = u'{}.{:01d}'.format(mph, decimal)
	
	row_max = max( row for row, col in speed_rc.iterkeys() ) + 1
	col_max = max( col for row, col in speed_rc.iterkeys() ) + 1
	
	speed_table = [ [ speed_rc[(row, col)] for col in xrange(col_max) ] for row in xrange(row_max) ]
	speed_table.reverse()
	
	return render( request, 'participant_est_speed_change.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantWaiverForm( Form ):
	def __init__(self, *args, **kwargs):
		super(ParticipantWaiverForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Waiver Correct and Signed'), css_class = 'btn btn-success' ),
			Submit( 'not-ok-submit', _('Waiver Incorrect or Unsigned'), css_class = 'btn btn-danger' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row(button_args[0]),
			Row(HTML('&nbsp')),
			Row(button_args[1]),
			Row(HTML('&nbsp')),
			Row(button_args[2]),
		)
		
@access_validation()
def ParticipantWaiverChange( request, participantId ):
	participant = get_participant( participantId )
	
	if request.method == 'POST':
		if 'ok-submit' in request.POST:
			participant.sign_waiver_now()
		elif 'not-ok-submit' in request.POST:
			participant.unsign_waiver_now()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantWaiverForm()
		
	return render( request, 'participant_waiver_change.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantTagForm( Form ):
	tag = forms.CharField( required = False, label = _('Tag') )
	make_this_existing_tag = forms.BooleanField( required = False, label = _('Rider keeps tag for other races') )
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label = _('RFID Antenna to Write Tag') )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantTagForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Update Tag in Database'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			Submit( 'auto-generate-tag-submit', _('Auto Generate Tag Only - Do Not Write'), css_class = 'btn btn-primary' ),
			Submit( 'write-tag-submit', _('Write Existing Tag'), css_class = 'btn btn-primary' ),
			Submit( 'auto-generate-and-write-tag-submit', _('Auto Generate and Write Tag'), css_class='btn btn-success' ),
		]
		
		self.helper.layout = Layout(
			Row(
				Col( Field('tag', rows='2', cols='60'), 4 ),
				Col( Field('make_this_existing_tag'), 4 ),
				Col( Field('rfid_antenna'), 4 ),
			),
			HTML( '<br/>' ),
			Row(
				button_args[4],
				HTML( '&nbsp;' * 5 ),
				button_args[3],
			),
			HTML( '<br/>' * 2 ),
			Row(
				button_args[2],
			),
			HTML( '<br/>' * 2 ),
			Row( 
				button_args[0],
				HTML( '&nbsp;' * 5 ),
				button_args[1],
			),
		)

def get_bits_from_hex( s ):
	return len(s or '') * 4
		
@access_validation()
def ParticipantTagChange( request, participantId ):
	participant = get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	system_info = SystemInfo.get_singleton()
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = ParticipantTagForm( request.POST )
		if form.is_valid():
			status = True
			status_entries = []

			tag = form.cleaned_data['tag'].strip().upper()
			make_this_existing_tag = form.cleaned_data['make_this_existing_tag']
			rfid_antenna = request.session['rfid_antenna'] = int(form.cleaned_data['rfid_antenna'])
			
			if 'auto-generate-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				if (	competition.use_existing_tags and
						system_info.tag_creation == 0 and get_bits_from_hex(license_holder.existing_tag) == system_info.tag_bits):
					tag = license_holder.existing_tag
				else:
					tag = license_holder.get_unique_tag()
				
			if not tag:
				status = False
				status_entries.append(
					(_('Empty Tag'), (
						_('Cannot write an empty Tag to the Database.'),
						_('Please specify a Tag, generate a Tag, or press Cancel.'),
					)),
				)
			elif not utils.allHex(tag):
				status = False
				status_entries.append(
					(_('Non-Hex Characters in Tag'), (
						_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
						_('Please change the Tag to all hexadecimal.'),
					)),
				)
			if not status:
				return render( request, 'rfid_write_status.html', locals() )
			
			participant.tag = tag
			try:
				participant.auto_confirm().save()
			except IntegrityError as e:
				# Report the error - probably a non-unique field.
				has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
				status = False
				status_entries.append(
					(_('Participant Save Failure'), (
						u'{}'.format(e),
					)),
				)
				return render( request, 'rfid_write_status.html', locals() )
			
			if make_this_existing_tag:
				license_holder.existing_tag = tag
				try:
					license_holder.save()
				except Exception as e:
					# Report the error - probably a non-unique field.
					status = False
					status_entries.append(
						(string_concat(_('LicenseHolder'), u': ', _('Existing Tag Save Exception:')), (
							unicode(e),
						)),
					)
					return render( request, 'rfid_write_status.html', locals() )
			
			if 'write-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				if not rfid_antenna:
					status = False
					status_entries.append(
						(_('RFID Antenna Configuration'), (
							_('RFID Antenna for Tag Write must be specified.'),
							_('Please specify the RFID Antenna.'),
						)),
					)
				
				if status:
					status, response = WriteTag(tag, rfid_antenna)
					if not status:
						status_entries = [
							(_('Tag Write Failure'), response.get('errors',[]) ),
						]
				
				if not status:
					return render( request, 'rfid_write_status.html', locals() )
				# if status: fall through to ok-submit case.
			
			# ok-submit
			if 'auto-generate-tag-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'path'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantTagForm( initial = dict(tag=participant.tag, rfid_antenna=rfid_antenna, make_this_existing_tag=competition.use_existing_tags) )
		
	return render( request, 'participant_tag_change.html', locals() )
	
#-----------------------------------------------------------------------

@autostrip
class ParticipantSignatureForm( Form ):
	signature = forms.CharField( required = False, label = _('Signature') )
	
	def __init__(self, *args, **kwargs):
		is_jsignature = kwargs.pop( 'is_jsignature', True )
		super(ParticipantSignatureForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_id = 'id_signature_form'
		self.helper.form_class = 'navbar-form navbar-left'
		
		if is_jsignature:
			button_args = [
				Submit( 'ok-submit', ('&nbsp;'*10) + unicode(_('OK')) + ('&nbsp;'*10), css_class = 'btn btn-success', style='font-size:200%' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning hidden-print', style='font-size:200%' ),
				HTML(u'<button class="btn btn-warning hidden-print" onClick="reset_signature()">{}</button>'.format(_('Reset'))),
			]
		else:
			button_args = [
				HTML('&nbsp;'*24),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning hidden-print', style='font-size:150%' )
			]
		
		if is_jsignature:
			self.helper.layout = Layout(
				Container(
					Row( Col(Field('signature'), 12) ),
					Row( Col(Div(id="id_signature_canvas"), 12) ),

					Row(
						Col(button_args[0],4),
						Col(button_args[1],4),
						Col(button_args[2],4),
					),
				)
			)
		else:
			self.helper.layout = Layout(
				Container(
					Row( Col( Field( 'signature' ), 12) ),
					Row( Div( Div(*button_args, css_class='row'), css_class='col-md-12 text-center' ) ),
				)
			)

@access_validation()
def ParticipantSignatureChange( request, participantId ):
	participant = get_participant( participantId )
	signature_with_touch_screen = int(request.session.get('signature_with_touch_screen', True))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantSignatureForm( request.POST, is_jsignature=signature_with_touch_screen )
		if form.is_valid():
			signature = form.cleaned_data['signature']
			signature = signature.strip()
			if not signature:
				return HttpResponseRedirect(getContext(request,'path'))
				
			participant.signature = signature
			participant.auto_confirm().save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantSignatureForm( is_jsignature=signature_with_touch_screen )
	
	if signature_with_touch_screen:
		return render( request, 'participant_jsignature_change.html', locals() )
	else:
		return render( request, 'participant_signature_change.html', locals() )
	
@access_validation()
def SetSignatureWithTouchScreen( request, use_touch_screen ):
	request.session['signature_with_touch_screen'] = bool(int(use_touch_screen))
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------

@access_validation()
def ParticipantBarcodeAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	add_by_barcode = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = BarcodeScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
			scan = form.cleaned_data['scan'].strip()
			if not scan:
				return HttpResponseRedirect(getContext(request,'path'))
				
			license_holder, participants = participant_key_filter( competition, scan, False )
			license_holders = []	# Required for participant_scan_error.
			if not license_holder:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(participants) == 1:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			if len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holder.id))
	else:
		form = BarcodeScanForm( hide_cancel_button=True )
		
	return render( request, 'participant_scan_form.html', locals() )
	
@access_validation()
def ParticipantNotFound( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_not_found.html', locals() )
	
@access_validation()
def ParticipantMultiFound( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_multi_found.html', locals() )
	
#-----------------------------------------------------------------------

@access_validation()
def ParticipantRfidAdd( request, competitionId, autoSubmit=False ):
	competition = get_object_or_404( Competition, pk=competitionId )
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	status = True
	status_entries = []
	tag = None
	tags = []
	
	add_by_rfid = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = RfidScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
		
			request.session['rfid_antenna'] = rfid_antenna = int(form.cleaned_data['rfid_antenna'])
			
			if not rfid_antenna:
				status = False
				status_entries.append(
					(_('RFID Antenna Configuration'), (
						_('RFID Antenna for Tag Read must be specified.'),
						_('Please specify the RFID Antenna.'),
					)),
				)
			else:
				status, response = ReadTag(rfid_antenna)
				# DEBUG DEBUG
				#status, response = True, {'tags': ['A7A2102303']}
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
					status_entries.append(
						(_('Multiple Tags Read'), tags ),
					)
			
			if not status:
				return render( request, 'participant_scan_rfid.html', locals() )
				
			license_holder, participants = participant_key_filter( competition, tag, False )
			license_holders = []	# Required for participant_scan_error.
			if not license_holder:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(participants) == 1:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			if len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holder.id))
	else:
		form = RfidScanForm( initial=dict(rfid_antenna=rfid_antenna), hide_cancel_button=True )
		
	return render( request, 'participant_scan_rfid.html', locals() )

