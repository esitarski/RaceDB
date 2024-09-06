import uuid
from subprocess import Popen, PIPE
import traceback
import operator

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .views_common import *
from .views import BarcodeScanForm, RfidScanForm
from .get_id import get_id
from .CountryIOC import ioc_country
from .print_bib import print_bib_tag_label, print_id_label, print_body_bib, print_shoulder_bib
from .participant_key_filter import participant_key_filter, participant_bib_filter
from .get_participant_excel import get_participant_excel
from .emails import show_emails
from .gs_cmd import gs_cmd
from .ReadWriteTag import ReadTag, WriteTag

def get_participant( participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	return participant.enforce_tag_constraints()

@autostrip
class ParticipantSearchForm( Form ):
	scan = forms.CharField( required=False, label = _('Scan Search'), help_text=_('Searches License and RFID Tag only') )
	event = forms.ChoiceField( required=False, label = _('Event'), help_text=_('For faster response, review one Event at a time') )
	name_text = forms.CharField( required=False, label = _('Name') )
	gender = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('Men')), (1, _('Women'))), initial = 2 )
	category = forms.ChoiceField( required=False, label = _('Category') )
	bib = forms.IntegerField( required=False, min_value = -1 , label=_('Bib (-1 for Missing)') )
	rfid_text = forms.CharField( required=False, label = _('RFIDTag (-1 for Missing)') )
	eligible = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Eligible') )	
	license_checked = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Lic. Check') )
	paid = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Paid') )
	confirmed = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Confirmed') )

	team_text = forms.CharField( required=False, label = _('Team (-1 for Independent)') )
	role_type = forms.ChoiceField( required=False, label = _('Role Type')  )
	
	city_text = forms.CharField( required=False, label = _('City') )
	state_prov_text = forms.CharField( required=False, label = _('State/Prov') )
	nationality_text = forms.CharField( required=False, label = _('Nationality') )
	
	complete = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Complete') )
	
	has_events = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('None')), (1, _('Some'))), label = _('Has Events') )
	
	def __init__(self, *args, **kwargs):
		competition = kwargs.pop( 'competition', None )
		super().__init__(*args, **kwargs)
		
		if competition:
			self.fields['category'].choices = \
				[(-1, '----')] + [(-2, _('*** Missing ***'))] + [(category.id, category.code_gender) for category in competition.get_categories()]
			events = sorted( competition.get_events(), key = operator.attrgetter('date_time') )
			self.fields['event'].choices = \
				[('-1.0', _('All'))] + [('{}.{}'.format(event.event_type, event.id), '{} {}'.format(event.short_name, timezone.localtime(event.date_time).strftime('%Y-%m-%d %H:%M:%S'))) for event in events]
			
		roleChoices = [(i, role) for i, role in enumerate(Participant.ROLE_NAMES)]
		roleChoices[0] = (0, '----')
		self.fields['role_type'].choices = roleChoices
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'clear-submit', _('Clear Search'), css_class = 'btn btn-primary' ),
			CancelButton( _('OK'), css_class='btn btn-primary' ),
			Submit( 'emails-submit', _('Emails'), css_class = 'btn btn-primary' ),
			Submit( 'export-excel-submit', _('Export to Excel'), css_class = 'btn btn-primary' ),

			Submit( 'reset-bibs-submit', _('Reset Bibs'), css_class = 'btn btn-warning' ),
			Submit( 'reset-tags-submit', _('Reset Tags'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('scan', size=20, autofocus=True ), HTML('&nbsp;'*8), Field('event'),),
			Row( *(
					[Field('name_text'), Field('gender'), Field('category'), Field('bib', size=7),] +
					([Field('rfid_text', size=16),] if competition and competition.using_tags else []) +
					[Field('eligible'), Field('license_checked'), Field('paid'), Field('confirmed'), Field('team_text'), Field('role_type'),] +
					[Field('city_text'), Field('state_prov_text', size=12), Field('nationality_text', size=12), ] + 
					[Field('complete'), Field('has_events'), ]
				)
			),
			Row( *(button_args[:-4] + [HTML('&nbsp;'*8)] + button_args[-4:]) ),
		)

@access_validation()
def Participants( request, competitionId ):
	ParticipantsPerPage = 50
	
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
		if 'clear-submit' in request.POST:
			request.session[pfKey] = {}
			request.session[pageKey] = None
			return HttpResponseRedirect(getContext(request,'path'))
			
		form = ParticipantSearchForm( request.POST, competition=competition )
		if form.is_valid():
			participant_filter = form.cleaned_data
			request.session[pfKey] = participant_filter
			request.session[pageKey] = None
	else:
		form = ParticipantSearchForm( competition = competition, initial = participant_filter )
	
	#-------------------------------------------------------------------
	
	event = None
	try:
		event_type, event_pk = [int(v) for v in participant_filter.get('event', '-1.0').split('.')]
	except Exception:
		event_type, event_pk = None, None
	if event_type == 0:
		event = competition.eventmassstart_set.filter(pk=event_pk).first()
	elif event_type == 1:
		event = competition.eventtt_set.filter(pk=event_pk).first()
			
	participants = event.get_participants() if event else competition.participant_set.all()
	
	competitors = participants.filter( role=Participant.Competitor )
	missing_category_count = competitors.filter( category__isnull=True ).count()
	missing_bib_count = competitors.filter( bib__isnull=True ).count()
	
	if competition.using_tags:
		if competition.do_tag_validation:
			# Show checked tags.
			bad_tag_query = Q(tag_checked=False)
		else:
			# Show empty tags.
			if competition.use_existing_tags:
				bad_tag_query = Q(license_holder__existing_tag__isnull=True) | Q(license_holder__existing_tag='')
			else:
				bad_tag_query = Q(tag__isnull=True) | Q(tag='')
	else:
		bad_tag_query = Q()
	
	bad_tag_count = competitors.filter( bad_tag_query ).count() if competition.using_tags else 0
	
	if participant_filter.get('scan',0):
		name_text = utils.normalizeSearch( participant_filter['scan'] )
		names = name_text.split()
		if names:
			q = Q()
			if names[0].startswith('^') and len(names[0]) >= 2:
				q &= Q(license_holder__last_name__istartswith = names[0][1:])
				names = names[1:]
			for n in names:
				q &= Q(license_holder__search_text__icontains = n)
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
				participants = participants.filter( license_holder__search_text__icontains=n )
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
		if team_search == '-1' or Team.is_independent_name(team_search):
			participants = participants.filter( team__isnull = True )
		else:
			participants = participants.filter( team__isnull = False )
			q = Q()
			for t in team_search.split():
				q &= Q( team__search_text__icontains=t )
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
		if rfid == '-1':
			participants = participants.filter( bad_tag_query )
		else:
			if competition.use_existing_tags:
				participants = participants.filter( license_holder__existing_tag=rfid )
			else:
				participants = participants.filter( tag=rfid )
	
	# Get all categories that require a license check.
	category_requires_license_check_query = CompetitionCategoryOption.objects.filter( competition=competition, license_check_required=True ).values_list('category__id', flat=True)
	category_requires_license_check = set( category_requires_license_check_query )
	if category_requires_license_check and competition.report_label_license_check:
		license_holder_license_checked = set(
			# Get all participants that have had their license checked at previous competitions in the last year.
			Participant.objects.filter(
				id__in=participants.values_list('id', flat=True),
				license_checked=True,
				category__id__in=category_requires_license_check_query,
				competition__discipline__id=competition.discipline_id,
				competition__start_date__gte=datetime.date(competition.start_date.year,1,1),
				competition__start_date__lte=competition.start_date,
				competition__report_label_license_check=competition.report_label_license_check,
			).exclude( competition=competition ).order_by().values_list('category__id', 'license_holder__id').iterator()
		) | set(
			# Check all participante that have had their license check logged in the last year.
			LicenseCheckState.objects.filter(
				license_holder__id__in=participants.values_list('license_holder__id', flat=True),
				category__id__in=category_requires_license_check_query,
				discipline__id=competition.discipline_id,
				report_label_license_check=competition.report_label_license_check,
				check_date__gte=datetime.date(competition.start_date.year,1,1),
				check_date__lte=competition.start_date,
			).order_by().values_list('category__id', 'license_holder__id').iterator()
		)
		
		# Set the current license check flag based on whether it was set in previous events.
		cat_lh = defaultdict( list )
		for category_id, license_holder_id in license_holder_license_checked:
			cat_lh[category_id].append( license_holder_id )
		# For each category, update the license holders to the status of the past license check.
		for category_id, license_holders in cat_lh.items():
			Participant.objects.filter( category__id=category_id, license_holder__id__in=license_holders ).exclude( participant.license_checked ).update( license_checked=True )
	else:
		license_holder_license_checked = set()
	
	requires_license_check = bool(category_requires_license_check)
	
	def is_license_checked_html( participant ):
		''' Returns: 1: Yes, 0: No, -1: Unnecessary '''
		if not participant.category or participant.category_id not in category_requires_license_check:
			return ''
		if participant.license_checked or (participant.category_id, participant.license_holder_id) in license_holder_license_checked:
			return mark_safe('<span class="is-good"/>')
		else:
			return mark_safe('<span class="is-bad"/>')

	if requires_license_check:
		license_checked = int(participant_filter.get('license_checked', 2))
		if license_checked == 1:
			participants = participants.filter( license_checked=True )
		elif license_checked == 0:
			participants = participants.filter( license_checked=False )

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
			
		if 'reset-bibs-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'ParticipantsResetBibs', competition.id) )
		
		if 'reset-tags-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'ParticipantsResetTags', competition.id) )
			
	participants, paginator = getPaginator( participants )
	return render( request, 'participant_list.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def ParticipantsResetBibs( request, competitionId, confirmed=False ):
	competition = get_object_or_404( Competition, pk=competitionId )	
	
	if confirmed:
		competition.participant_set.exclude(bib__isnull=True).update( bib=None )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Reset All Participant Bibs')
	message = _('Reset the bibs of all participants in this Competition to null (no value).  This applies to this competition only and will not change the permanent bib number.')
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'ParticipantsResetBibs/{}/1/'.format(competition.id)
	return render( request, 'are_you_sure.html', locals() )

@access_validation()
def ParticipantsResetTags( request, competitionId, confirmed=False ):
	competition = get_object_or_404( Competition, pk=competitionId )	

	if confirmed:
		competition.participant_set.exclude(Q(tag__isnull=True) & Q(tag2__isnull=True)).update( tag=None, tag2=None, tag_checked=False )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Reset All Participant Tags')
	message = _('Reset the RFID tags of all participants to null (no value).  This applies to this competition only and will not change the permanent RFID tag value.')
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'ParticipantsResetTags/{}/1/'.format(competition.id)
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantsInEvents( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	competition_events = sorted( competition.get_events(), key=operator.attrgetter('date_time') )
	event_participants = { event:set(event.get_participants()) for event in competition_events }
	participants = sorted( set.union(*[p for p in event_participants.values()]), key=lambda p: p.license_holder.search_text )
	
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
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			CancelButton(),
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
		form = BibScanForm( request.POST )
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
		form = BibScanForm()
	
	return render( request, 'participant_add_bib.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantManualAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	search_text = request.session.get('participant_new_filter', '')
	btns = [('new-submit', 'New License Holder', 'btn btn-success')]
	add_by_manual = True
	if request.method == 'POST':	
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'ParticipantNotFound', competition.id) )
			
		form = SearchForm( btns, request.POST, hide_cancel_button=True )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['participant_new_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text}, hide_cancel_button=True )
	
	search_text = utils.normalizeSearch( search_text )
	q = Q( active = True )
	for term in search_text.split():
		q &= Q(search_text__icontains = term)
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
		# Get all deferred fields before participant copy.
		participant.refresh_from_db( fields=participant.get_deferred_fields() )
		participant.category = None
		participant.role = Participant.Competitor
		participant.bib = None
		participant.id = None
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
	try:
		participant = Participant.objects.get( pk=participantId )
	except Exception:
		return HttpResponseRedirect(getContext(request,'cancelUrl'))		
	competition = participant.competition
	participant.enforce_tag_constraints()

	system_info = SystemInfo.get_singleton()
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	
	competition_age = competition.competition_age( participant.license_holder )
	is_suspicious_age = not (5 <= competition_age <= 95)
	is_license_checked = participant.is_license_checked()
	is_license_check_required = participant.is_license_check_required()
	
	tag_ok = request.user.is_superuser or not competition.using_tags or not competition.do_tag_validation or participant.tag_checked
	#tag_ok = not competition.using_tags or not competition.do_tag_validation or participant.tag_checked
	
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
	participant.enforce_tag_constraints()
	return ParticipantEdit( request, participant.id )
	
@access_validation()
def ParticipantRemove( request, participantId ):
	participant = get_participant( participantId )
	participant.enforce_tag_constraints()
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
	
def print_pdf( request, participant, pdf_bytes, print_type ):
	system_info = SystemInfo.get_singleton()
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, print_type )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_bytes )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_bytes )
			returncode = p.returncode
		except Exception as e:
			stdout_info, stderr_info = '', e
			returncode = None
		
		try:
			os.remove( tmp_file )
		except Exception:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_bytes, content_type="application/pdf")
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
def ParticipantPrintBibLabel1( request, participantId ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_bib_tag_label(participant, right_page=False), 'Frame' )
	
@access_validation()
def ParticipantPrintShoulderBib( request, participantId ):
	participant = get_participant( participantId )
	return print_pdf( request, participant, print_shoulder_bib(participant), 'Shoulder' )
	
@access_validation()
def ParticipantPrintAllBib( request, participantId ):
	participant = get_participant( participantId )
	c = participant.competition
	
	ret = None
	if c.bibs_label_print:
		ret = ParticipantPrintBodyBib( request, participantId, 2 )
	elif c.bib_label_print:
		ret = ParticipantPrintBodyBib( request, participantId, 1 )
	
	if c.bibs_laser_print:
		ret = ParticipantPrintBodyBib( request, participantId, 2, 1 )
		
	if c.shoulders_label_print:
		ret = ParticipantPrintShoulderBib( request, participantId )
		
	if c.frame_label_print:
		ret = ParticipantPrintBibLabels( request, participantId )
	elif c.frame_label_print_1:
		ret = ParticipantPrintBibLabel1( request, participantId )
	
	return ret
	
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
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			CancelButton(),
		]
		
		self.helper.layout = Layout(
			HTML( '{}:&nbsp;&nbsp;&nbsp;&nbsp;'.format( _("Search") ) ),
			Div( Field('gender', css_class = 'form-control'), css_class = 'form-group' ),
			HTML( '&nbsp;&nbsp;&nbsp;&nbsp;' ),
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
	category = get_object_or_404( Category, pk=categoryId ) if int(categoryId) else None
	
	category_changed = (participant.category != category)
	if category and category_changed:
		categories = set( p.category
			for p in Participant.objects.filter(
				competition=competition, license_holder=participant.license_holder).exclude(
				category__isnull=True).select_related('category')
		)
		if category in categories:
			has_error, conflict_explanation, conflict_participant = True, _('LicenseHolder is already participating in this Category.'), None
			return render( request, 'participant_integrity_error.html', locals() )
		
		categories.discard( participant.category )
		categories.add( category )
	
		is_category_conflict, category_conflict_event, category_conflict_categories = competition.is_category_conflict(categories)
		if is_category_conflict:
			has_error, conflict_explanation, conflict_participant = True, _('Cannot assign to another Category that already exists in an Event.'), None
			categories = sorted(categories, key=lambda c: c.sequence)
			category_conflict_categories = sorted(category_conflict_categories, key=lambda c: c.sequence)
			return render( request, 'participant_integrity_error.html', locals() )
	
	participant.category = category
	if category and participant.role != Participant.Competitor:
		participant.role = Participant.Competitor
	
	participant.update_bib_new_category()
	
	if category_changed:
		participant.license_checked = False
	
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
def ParticipantLicenseCheckChange( request, participantId ):
	participant = get_participant( participantId )
	cco = CompetitionCategoryOption.objects.filter( competition=participant.competition, category=participant.category ).first()
	note = cco.note if cco else ''
	return render( request, 'participant_license_check_select.html', locals() )

@access_validation()
def ParticipantLicenseCheckSelect( request, participantId, status ):
	participant = get_participant( participantId )
	participant.license_checked = bool(int(status))
	if not participant.license_checked:
		LicenseCheckState.uncheck_participant( participant )
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
		q &= Q( search_text__icontains = n )
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

def get_ioc_countries():
	countries = [(name, code) for code, name in ioc_country.items()]
	countries.sort( key=operator.itemgetter(1) )
	return countries

@access_validation()
def LicenseHolderNationCodeSelect( request, licenseHolderId, iocI ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	iocI = int(iocI)
	if iocI < 0:
		license_holder.nation_code = ''
	else:
		license_holder.nation_code = get_ioc_countries()[iocI][-1]
	license_holder.save()
	return HttpResponseRedirect(getContext(request,'popUrl'))

@access_validation()
def LicenseHolderNationCodeChange( request, licenseHolderId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	countries = [[i, flag_html(c[-1])] + list(c) for i, c in enumerate(get_ioc_countries())]
	flag_instance = ''
	code_instance = ''
	name_instance = ''
	for c in countries:
		if c[-1] == license_holder.nation_code:
			flag_instance = c[1]
			ioc_instance = c[-1]
			name_instance = c[-2]
			break
	rows = []
	cols = 4
	for i in range(0, len(countries), cols):
		rows.append( countries[i:i+cols] )
	return render( request, 'license_holder_nation_code_select.html', locals() )

@autostrip
class TeamDisciplineForm( Form ):
	disciplines = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple,)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.fields['disciplines'].choices = [(d.id, d.name) for d in Discipline.objects.all()]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = ''
		
		buttons = [
			Submit( 'set-all-submit', _('Same Team for All Disciplines'), css_class = 'btn btn-primary' ),
			Submit( 'set-selected-submit', _('Team for Selected Disciplines Only'), css_class = 'btn btn-primary' ),
			CancelButton(),
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
		disciplines = []
		if 'set-all-submit' in request.POST:
			disciplines = list( Discipline.objects.all().values_list('id', flat=True) )
		elif 'set-selected-submit' in request.POST:
			form = TeamDisciplineForm( request.POST )
			if form.is_valid():
				disciplines = form.cleaned_data['disciplines']

		participant.team = team
		participant.auto_confirm().save()
		
		# First, delete all existing teams for the given disciplines.
		TeamHint.objects.filter( discipline__id__in=disciplines, license_holder=participant.license_holder ).delete()

		if team:
			today = timezone.localtime(timezone.now()).date()
			to_create = []
			for id in disciplines:
				th = TeamHint( license_holder=participant.license_holder, team=team ,effective_date=today )
				th.discipline_id = id
				to_create.append( th )	
			TeamHint.objects.bulk_create( to_create )
			
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
	
	available_numbers, allocated_numbers, lost_bibs, category_numbers_defined = participant.get_available_numbers()
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
			except Exception:
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
	
	def done():
		return HttpResponseRedirect(getContext(request,'pop2Url'))
	def showSelectAgain():
		return HttpResponseRedirect(getContext(request,'popUrl'))
	
	bib_save = participant.bib
	bib = int(bib)
	
	# No change - nothing to do.
	if bib == bib_save:
		return done()
	
	if competition.number_set and bib_save is not None:
		def set_lost():
			competition.number_set.set_lost( bib_save, participant.license_holder )
	else:
		def set_lost():
			pass
	
	# Bib assigned "No Bib".
	if bib < 0:
		participant.bib = None
		set_lost()
		return done()
	
	# Assign new Bib.
	participant.bib = bib
	
	# Check for conflict in events.
	if participant.category:
		bib_conflicts = participant.get_bib_conflicts()
		if bib_conflicts:
			# If conflict, restore the previous bib and repeat.
			participant.bib = bib_save
			return showSelectAgain()

	set_lost()
	
	try:
		participant.auto_confirm().save()
	except IntegrityError as e:
		# Assume the Integrity Error is due to a race condition with the bib number.
		return showSelectAgain()
	
	return done()

#-----------------------------------------------------------------------
@autostrip
class ParticipantNoteForm( Form ):
	note = forms.CharField( widget = forms.Textarea, required = False, label = _('Note') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
			CancelButton(),
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
	choices = [(event.option_id, '{} ({})'.format(event.name, event.get_event_type_display()))
					for event, is_participating in participation_optional_events]
	
	@autostrip
	class ParticipantOptionForm( Form ):
		options = forms.MultipleChoiceField( required = False, label = _('Optional Events'), choices=choices )
		
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				CancelButton(),
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

def GetParticipantEstSpeedForm( participant ):
	competition = participant.competition
	km = participant.get_tt_km()
	
	@autostrip
	class ParticipantEstSpeedForm( Form ):
		est_speed = forms.FloatField( required = False,
			label=format_lazy('{} ({})', _('Estimated Speed for Time Trial'), competition.speed_unit_display),
			help_text=_('Enter a value or choose from the grid below.')
		)
		if km:
			est_duration = DurationField.DurationFormField( required = False,
			label=format_lazy('{} ({})', _('or Estimated Time for Time Trial'), participant.get_tt_distance_text() ),
			help_text=_('In [HH:]MM:SS format.')
		)
		seed_option = forms.ChoiceField( required = False, choices=Participant.SEED_OPTION_CHOICES, label=_('Seed Option'),
			help_text=_('Tells RaceDB to start this rider as Early or as Late as possible in the Start Wave')
		)
		
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				CancelButton(),
			]
			
			self.helper.layout = Layout(
				Row(
					Col(Field('est_speed', css_class = 'form-control', size = '20'), 4),
					Col(Field('est_duration'), 4) if km else HTML(''),
					Col(Field('seed_option'), 4),
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
		form = GetParticipantEstSpeedForm(participant)( request.POST )
		if form.is_valid():
			est_speed = form.cleaned_data['est_speed']
			participant.est_kmh = competition.to_kmh( est_speed or 0.0 )
			participant.seed_option = form.cleaned_data['seed_option']
			participant.save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = GetParticipantEstSpeedForm(participant)(
			initial = dict( est_speed=competition.to_local_speed(participant.est_kmh), seed_option=participant.seed_option )
		)
	
	speed_rc = {}
	if competition.distance_unit == 0:
		for col, kmh in enumerate(range(20, 51)):
			for row, decimal in enumerate(range(0, 10)):
				speed_rc[(col, row)] = '{}.{:01d}'.format(kmh, decimal)
	else:
		for col, mph in enumerate(range(12, 32)):
			for row, decimal in enumerate(range(0, 10)):
				speed_rc[(col, row)] = '{}.{:01d}'.format(mph, decimal)
	
	row_max = max( row for row, col in speed_rc.keys() ) + 1
	col_max = max( col for row, col in speed_rc.keys() ) + 1
	
	speed_table = [ [ speed_rc[(row, col)] for col in range(col_max) ] for row in range(row_max) ]
	speed_table.reverse()
	
	return render( request, 'participant_est_speed_change.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantWaiverForm( Form ):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Waiver Correct and Signed'), css_class = 'btn btn-success' ),
			Submit( 'not-ok-submit', _('Waiver Incorrect or Unsigned'), css_class = 'btn btn-danger' ),
			CancelButton(),
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
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label = _('RFID Antenna') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Update Tag in Database'), css_class = 'btn btn-primary' ),
			CancelButton(),
			Submit( 'auto-generate-tag-submit', _('Auto Generate Tag Only - Do Not Write'), css_class = 'btn btn-primary' ),
			Submit( 'write-tag-submit', _('Write Existing Tag'), css_class = 'btn btn-primary' ),
			Submit( 'auto-generate-and-write-tag-submit', _('Auto Generate and Write Tag'), css_class='btn btn-success' ),
			Submit( 'check-tag-submit', _('Check Tag'), css_class = 'btn btn-lg btn-block btn-success' ),
			Submit( 'associate-existing-tag-submit', _('Update Database from Tag'), css_class='btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Col(button_args[5], 8), Col(button_args[1], 4) ),
			Row( HTML('<hr style="margin:32px"/>') ),
			Row(
				Col( Field('tag', rows='2', cols='60'), 5 ),
				Col( Field('rfid_antenna'), 3 ),
			),
			HTML( '<br/>' ),
			Row(
				button_args[4], HTML( '&nbsp;' * 5 ),
				button_args[3], HTML( '&nbsp;' * 5 ),
				button_args[6],
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
	
	if not competition.has_rfid_reader():
		return ParticipantTagChangeUSBReader( request, participantId, participant=participant )
	
	make_this_existing_tag = competition.use_existing_tags
	license_holder = participant.license_holder
	system_info = SystemInfo.get_singleton()
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	validate_success = False
	
	status = True
	status_entries = []
	def check_antenna( rfid_antenna ):
		if not rfid_antenna:
			status_entries.append(
				(_('RFID Antenna Configuration'), (
					_('RFID Antenna must be specified.'),
					_('Please specify the RFID Antenna.'),
				)),
			)
			return False
		return True
	
	def check_empty_tag( tag ):
		if not tag:
			status_entries.append(
				(_('Empty Tag'), (
					_('Cannot validate an empty Tag.'),
					_('Please generate a Tag, or press Cancel.'),
				)),
			)
			return False
		return True

	def check_unique_tag( tag ):
		if make_this_existing_tag:
			lh = LicenseHolder.objects.filter( Q(existing_tag=tag) | Q(existing_tag2=tag) ).exclude( pk=license_holder.pk ).first()
			if lh:
				status_entries.append(
					(_('Duplicate Tag'), (
						_('Tag already in use by LicenseHolder.'),
						lh.__repr__(),
					)),
				)
				return False
		p = Participant.objects.filter( competition=competition ).filter( Q(tag=tag) | Q(tag2=tag) ).exclude( license_holder=license_holder ).first()
		if p:
			status_entries.append(
				(_('Duplicate Tag'), (
					_('Tag already in use by Participant.'),
					p.license_holder.__repr__(),
				)),
			)
			return False
		return True

	def check_one_tag_read( tags ):
		if not tags:
			status_entries.append(
				(_('Tag Read Failure'), (
					_('No tags read.  Verify antenna number and that tag is close to antenna.'),
				)),
			)
			return False
		if len(tags) > 1:
			status_entries.append(
				(_('Multiple Tags Read'), [add_name_to_tag(competition, t) for t in tags] ),
			)
			return False
		return True
		
	def participant_save( particiant ):
		try:
			participant.auto_confirm().save()
		except IntegrityError as e:
			# Report the error - probably a non-unique field.
			has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
			status_entries.append(
				(_('Participant Save Failure'), (
					'{}'.format(e),
				)),
			)
			return False
		return True
			
	if request.method == 'POST':
		form = ParticipantTagForm( request.POST )
		if form.is_valid():

			tag = form.cleaned_data['tag'].strip().upper()
			rfid_antenna = request.session['rfid_antenna'] = int(form.cleaned_data['rfid_antenna'])
			
			if 'check-tag-submit' in request.POST:
				status &= check_antenna(rfid_antenna) and check_empty_tag(tag)
				if status:
					status, response = ReadTag(rfid_antenna)
					if not status:
						status_entries = [
							(_('Tag Read Failure'), response.get('errors',[]) ),
						]
					else:
						tags = response.get('tags', [])
						status &= check_one_tag_read( tags )
						if status:
							tag_read = tags[0]
							if tag_read == tag:
								validate_success = True
								participant.tag_checked = True
								# Fallthrough so that the tag format is checked.
							else:
								status = False
								status_entries.append(
									(_('Tag Validation Failure'), [tag_read, _('***DOES NOT MATCH***'), tag] ),
								)								
								participant.tag_checked = False
								status &= participant_save( participant )
			
			elif 'auto-generate-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				participant.tag_checked = False
				if (	competition.use_existing_tags and
						system_info.tag_creation == 0 and get_bits_from_hex(license_holder.existing_tag) == system_info.tag_bits):
					tag = license_holder.existing_tag
				else:
					tag = license_holder.get_unique_tag( system_info )
			
			elif 'associate-existing-tag-submit' in request.POST:
				status &= check_antenna(rfid_antenna)
				if status:
					status, response = ReadTag(rfid_antenna)
					if not status:
						status_entries = [
							(_('Tag Read Failure'), response.get('errors',[]) ),
						]
					else:
						tags = response.get('tags', [])
						status &= check_one_tag_read( tags )
						if status:
							tag = tags[0]
							status &= check_unique_tag( tag, make_this_existing_tag )
							if status:
								participant.tag_checked = True
			
			if status:
				status &= check_empty_tag( tag )
				if status and system_info.tag_all_hex and not utils.allHex(tag):
					status = False
					status_entries.append(
						(_('Non-Hex Characters in Tag'), (
							_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
						)),
					)
			
			if not status:
				participant.tag_checked = False
				participant_save( participant )
				return render( request, 'rfid_write_status.html', locals() )
			
			participant.tag = tag
			participant.tag2 = None
			status &= participant_save( participant )
			if not status:
				return render( request, 'rfid_write_status.html', locals() )
			
			if make_this_existing_tag and license_holder.existing_tag != tag and license_holder.existing_tag2 != None:
				license_holder.existing_tag = tag
				license_holder.existing_tag2 = None
				try:
					license_holder.save()
				except Exception as e:
					# Report the error - probably a non-unique field.
					status = False
					status_entries.append(
						(
							format_lazy('{}: {}', _('LicenseHolder'), _('Existing Tag Save Exception:')),
							('{}'.format(e),)
						),
					)
					return render( request, 'rfid_write_status.html', locals() )
			
			if 'write-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				status &= check_antenna( rfid_antenna )
				
				if status:
					status, response = WriteTag(tag, rfid_antenna)
					if not status:
						participant.tag_checked = False
						participant_save( participant )
						status_entries = [
							(_('Tag Write Failure'), response.get('errors',[]) ),
						]
					else:
						participant.tag_checked = True
						status &= participant_save( participant )
				
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
class ParticipantTagUSBReaderForm( Form ):
	rfid_tag = forms.CharField( max_length=Participant._meta.get_field('tag').max_length, label=_('Tag') )
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-success' ),
			CancelButton(),
		]
		
		self.helper.layout = Layout(
			Row(
				Col( Field('rfid_tag', size='40'), 6 ),
			),
			HTML( '<br/>' ),
			Row( 
				button_args[0],
				HTML( '&nbsp;' * 5 ),
				button_args[1],
			),
		)

@access_validation()
def ParticipantTagChangeUSBReader( request, participantId, action=-1, participant=None ):
	participant = participant or get_participant( participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	system_info = SystemInfo.get_singleton()
	validate_success = False
	status = True
	status_entries = []
	
	action = int(action)
	
	path_noargs = getContext(request, 'cancelUrl') + 'ParticipantTagChangeUSBReader/'
	path_actions = '{}{}/'.format(path_noargs, participantId)
	
	participant.enforce_tag_constraints()
	
	rfid_tag1 = license_holder.existing_tag  if competition.use_existing_tags else participant.tag
	rfid_tag2 = license_holder.existing_tag2 if competition.use_existing_tags else participant.tag2
	
	if action < 0:
		title = _("RFID USB Reader")
		return render( request, 'participant_tag_change_usb_reader.html', locals() )
	else:
		title = [_("Validate Tag"), _("Issue Tag 1"),_("Issue Tag 2")][action]

	if competition.use_existing_tags:
		def check_unique_tag( tag ):
			lh = LicenseHolder.objects.filter( Q(existing_tag=tag) | Q(existing_tag2=tag) ).exclude( pk=license_holder.pk ).first()
			if lh:
				status_entries.append(
					(_('Duplicate Tag'), (
						_('Tag in use by LicenseHolder.'),
						lh.__repr__(),
					))
				)
				return False
			return True
	else:
		def check_unique_tag( tag ):
			p = Participant.objects.filter( competition=competition ).filter( Q(tag=tag) | Q(tag2=tag) ).exclude( license_holder=license_holder ).first()
			if p:
				status_entries.append(
					(_('Duplicate Tag'), (
						_('Tag in use by Participant.'), p.license_holder.__repr__())
					)
				)
				return False
			return True

	def participant_save( particiant ):
		try:
			participant.auto_confirm().save()
		except IntegrityError as e:
			# Report the error - probably a non-unique field.
			has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
			status_entries.append(
				(_('Participant Save Failure'), ('{}'.format(e),))
			)
			return False
		return True
		
	def license_holder_save( license_holder ):
		try:
			license_holder.save()
			return True
		except Exception as e:
			# Report the error - probably a non-unique field.
			status_entries.append(
				(
					format_lazy('{}: {}', _('LicenseHolder'), _('Save Exception:')),
					('{}'.format(e),)
				),
			)
			return False
			
	if request.method == 'POST':
		form = ParticipantTagUSBReaderForm( request.POST )
		if form.is_valid():
			rfid_tag = form.cleaned_data['rfid_tag'].upper().lstrip('0')
			
			try:
				if system_info.tag_all_hex and not utils.allHex(rfid_tag):
					status_entries.append(
						(_('Non-Hex Characters in Tag'), (
							_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
						)),
					)
					raise ValueError('tag contains non-hex characters')
				
				if not check_unique_tag( rfid_tag ):
					raise ValueError('tag is non unique')
				
				if action == 0:			# Validate tag.
					if competition.use_existing_tags:
						validate_success = (license_holder.existing_tag == rfid_tag or license_holder.existing_tag2 == rfid_tag)
					else:
						validate_success = (participant.tag == rfid_tag or participant.tag2 == rfid_tag)
					if not validate_success:
						status_entries.append(
							(_('Tag Validation Failure'), (_("***DOES NOT MATCH PARTICIPANT***"),) ),
						)
						if participant.tag_checked:
							participant.tag_checked = False
							participant_save( participant )
						raise RuntimeError('tag does not match participant')
					
					status_entries.append(
						(_('Tag Validation Success'), (_("***MATCHES PARTICIPANT***"),) ),
					)
					if not participant.tag_checked :
						participant.tag_checked = True
						if not participant_save( participant ):
							raise RuntimeError('participant save fails')
					
				elif action in (1, 2):		# Issue tag
					if not check_unique_tag( rfid_tag ):
						raise RuntimeError('tag is already in use')
					
					if competition.use_existing_tags:
						# Reset the tags for the participant in case of a license holder save failure.
						setattr( participant, ('tag', 'tag2')[action-1], None )
						participant.tag_checked = False
						participant_save( participant )
						
						# Set the existing tag for the license holder.
						setattr( license_holder, ('existing_tag', 'existing_tag2')[action-1], rfid_tag )
						if not license_holder_save( license_holder ):
							raise RuntimeError('license_holder save failure')
							
						# Update the participant tags.
						participant.tag = license_holder.existing_tag
						participant.tag2  = license_holder.existing_tag2
					else:
						# Set the tag for this participant only.
						setattr( participant, ('tag', 'tag2')[action-1], rfid_tag )
					
					# Mark as checked as we had to have read the tag to get this far.
					participant.tag_checked = True
					if not participant_save( participant ):
						raise RuntimeError('participant save failure')
						
			except Exception as e:
				status = False
								
			if not status_entries:
				return HttpResponseRedirect( path_actions )
	
	form = ParticipantTagUSBReaderForm( initial={'rfid_tag':''} )
		
	return render( request, 'participant_tag_change_usb_reader.html', locals() )
	
#-----------------------------------------------------------------------
@autostrip
class ParticipantSignatureForm( Form ):
	signature = forms.CharField( required = False, label = _('Signature') )
	
	def __init__(self, *args, **kwargs):
		is_jsignature = kwargs.pop( 'is_jsignature', True )
		super().__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_id = 'id_signature_form'
		
		if is_jsignature:
			button_args = [
				Submit( 'ok-submit', format_lazy( '{}{}{}', '&nbsp;'*10, _('OK'), '&nbsp;'*10), css_class = 'btn btn-success', style='font-size:200%' ),
				CancelButton( style='font-size:200%' ),
				HTML('<button class="btn btn-warning hidden-print" onClick="reset_signature()">{}</button>'.format(_('Reset'))),
			]
		else:
			button_args = [
				HTML('&nbsp;'*24),
				CancelButton( style='font-size:150%' )
			]
		
		if is_jsignature:
			self.helper.layout = Layout(
				Container(
					Row( Field('signature') ),
					Row( Div(id="id_signature_canvas") ),

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
					Row( Field('signature') ),
					Row( Div( Div(*button_args, css_class='row'), css_class='col-md-12 text-center' ) ),
				)
			)

@access_validation()
def ParticipantSignatureChange( request, participantId ):
	participant = get_participant( participantId )
	signature_with_touch_screen = int(request.session.get('signature_with_touch_screen', True))
	
	if request.method == 'POST':
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
		form = BarcodeScanForm( request.POST )
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
		form = BarcodeScanForm()
		
	return render( request, 'participant_scan_form.html', locals() )

'''	
@access_validation()
def ParticipantNotFoundError( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_not_found_error.html', locals() )
	
@access_validation()
def ParticipantMultiFoundError( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_multi_found_error.html', locals() )
'''
	
#-----------------------------------------------------------------------

@access_validation()
def ParticipantRfidAdd( request, competitionId, autoSubmit=False ):
	competition = get_object_or_404( Competition, pk=competitionId )
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	status = True
	status_entries = []
	rfid_tag = None
	rfid_tags = []
	
	add_by_rfid = True
	if request.method == 'POST':
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
				#status, response = True, {'rfid_tags': ['A7A2102303']}
				if not status:
					status_entries.append(
						(_('Tag Read Failure'), response.get('errors',[]) ),
					)
				else:
					rfid_tags = response.get('tags', [])
					try:
						rfid_tag = rfid_tags[0]
					except (AttributeError, IndexError) as e:
						status = False
						status_entries.append(
							(_('Tag Read Failure'), [e] ),
						)
				
				if rfid_tag and len(rfid_tags) > 1:
					status = False
					status_entries.append(
						(_('Multiple Tags Read'), rfid_tags ),
					)
			
			if not status:
				return render( request, 'participant_scan_rfid.html', locals() )
				
			license_holder, participants = participant_key_filter( competition, rfid_tag, False )
			license_holders = []	# Required for participant_scan_error.
			if not license_holder:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(participants) == 1:
				participants[0].set_tag_checked()
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			if len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holder.id, 1))
	else:
		form = RfidScanForm( initial=dict(rfid_antenna=rfid_antenna), hide_cancel_button=True )
		
	return render( request, 'participant_scan_rfid.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantConfirmForm( Form ):
	participant_id = forms.IntegerField()
	
	last_name = forms.CharField( label = _('Last Name') )
	first_name = forms.CharField( required=False, label = _('First Name') )
	date_of_birth = forms.DateField( label = _('Date of Birth'))
	nation_code = forms.CharField( max_length=3, required=False, label=_('Nation Code'), widget=forms.TextInput(attrs={'size': 3}) )
	gender = forms.ChoiceField( required=False, choices = ((0, _('Men')), (1, _('Women'))), label=_('Gender') )
	
	uci_id = forms.CharField( required=False, label=_('UCI ID') )
	license_code = forms.CharField( required=False, label=_('License Code') )
	
	category_name = forms.CharField( required=False, label = _('Category') )
	team_name = forms.CharField( required=False, label = _('Team') )
	confirmed = forms.BooleanField( required=False, label = _('Confirmed') )
	
	license_holder_fields = ('last_name', 'first_name', 'date_of_birth', 'nation_code', 'gender', 'uci_id', 'license_code')
	participant_fields = ('confirmed','category_name', 'team_name')
		
	def save( self, request ):
		participant = get_object_or_404( Participant, pk=self.cleaned_data['participant_id'] )
		license_holder = participant.license_holder

		for a in self.license_holder_fields:
			setattr( license_holder, a, self.cleaned_data[a] )
		license_holder.save()

		for a in self.participant_fields:
			if not a.endswith('_name'):
				setattr( participant, a, self.cleaned_data[a] )
		participant.save()
	
	@classmethod
	def get_initial( cls, participant ):
		license_holder = participant.license_holder
		initial = {}
		for a in cls.license_holder_fields:
			initial[a] = getattr( license_holder, a )
		for a in cls.participant_fields:
			if not a.endswith('_name'):
				initial[a] = getattr( participant, a )
		initial['category_name'] = participant.category_name
		initial['team_name'] = participant.team_name
		initial['participant_id'] = participant.id
		return initial
	
	def changeCategoryCB( self, request ):
		participant = get_object_or_404( Participant, pk=self.cleaned_data['participant_id'] )
		return HttpResponseRedirect( pushUrl(request, 'ParticipantCategoryChange', participant.id) )
		
	def changeTeamCB( self, request ):
		participant = get_object_or_404( Participant, pk=self.cleaned_data['participant_id'] )
		return HttpResponseRedirect( pushUrl(request, 'ParticipantTeamChange', participant.id) )
		
	def changeNationCodeCB( self, request ):
		participant = get_object_or_404( Participant, pk=self.cleaned_data['participant_id'] )
		return HttpResponseRedirect( pushUrl(request, 'LicenseHolderNationCodeChange', participant.license_holder_id) )
	
	def dispatch( self, request ):
		for ab in self.additional_buttons:
			if ab[3:] and ab[0] in request.POST:
				self.save( request )
				return ab[3]( request )
	
	def submit_button( self, ab ):
		name, value, cls = ab[:3]
		return Submit(name, value, css_class = cls + ' hidden-print')
	
	def __init__(self, *args, **kwargs):
		participant = kwargs.pop( 'participant', None )
		competition = participant.competition
		license_holder = participant.license_holder
		super().__init__(*args, **kwargs)
		
		self.fields['category_name'].widget.attrs['readonly'] = True
		self.fields['team_name'].widget.attrs['readonly'] = True
			
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'save-submit', _('Save'), css_class = 'btn btn-primary' ),
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
			CancelButton(),
		]
		
		change_team = ('change-team-submit', _('Change'), 'btn btn-primary', self.changeTeamCB)
		change_nation_code = ('change-nation-code-submit', _('Lookup'), 'btn btn-primary', self.changeNationCodeCB)
		change_category = ('change-category-submit', _('Change'), 'btn btn-primary', self.changeCategoryCB)
		self.additional_buttons = (change_team, change_nation_code, change_category)
		
		nation_code_error = license_holder.nation_code_error
		if not license_holder.uci_id:
			uci_id_error = 'missing'
		else:
			uci_id_error = license_holder.uci_id_error
		
		def warning_html( warning ):
			return '<img src="{}" style="width:20px;height:20px;"/>{}'.format(static('images/warning.png'), warning) if warning else ''

		self.helper.layout = Layout(
			Row( button_args[0], HTML('&nbsp;'*8), button_args[1], HTML('&nbsp;'*8), button_args[2] ),
			Row( HTML('<hr/>') ),
			Row( HTML('<div style="font-size: 125%;">'), Field('confirmed'), HTML('</div>') ),
			Row(
				Field('last_name', size=50, css_class='no-highlight'),
				Field('first_name', size=20, css_class='no-highlight'),
				Field('date_of_birth', size=10, css_class='no-highlight'),
			),
			Row(
				HTML(warning_html(nation_code_error)),
				HTML(flag_html(license_holder.nation_code) + ' ' + ioc_country.get(license_holder.nation_code, '')),
				FieldWithButtons(Field('nation_code', css_class='no-highlight'), self.submit_button(change_nation_code) ),
				HTML('&nbsp;'*2), Field('gender', css_class='no-highlight'),
				HTML('&nbsp;'*2), FieldWithButtons(Field('team_name', size=40, css_class='no-highlight'), self.submit_button(change_team) ),
			),
			Row(
				HTML(warning_html(uci_id_error)),
				Field('uci_id', size=15, css_class='no-highlight'), Field('license_code', css_class='no-highlight'),
				HTML('&nbsp;'*2), FieldWithButtons(Field('category_name', size=30, css_class='no-highlight'), self.submit_button(change_category) ),
			),
			Field('participant_id', type='hidden'),
		)

@access_validation()
def ParticipantConfirm( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition_age = participant.competition.competition_age( participant.license_holder )
	
	if request.method == 'POST':		
		form = ParticipantConfirmForm( request.POST, participant=participant )
		if form.is_valid():
			form.save( request )
			
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( '.' )
		
			if 'ok-submit' in request.POST:
				participant.confirmed = True
				participant.save()
				return HttpResponseRedirect( getContext(request,'cancelUrl') )
			return form.dispatch( request )
	else:
		form = ParticipantConfirmForm( initial=ParticipantConfirmForm.get_initial(participant), participant=participant )

	return render( request, 'participant_confirm.html', locals() )
	
#--------------------------------------------------------------------------------------

@autostrip
class ParticipantNotFoundForm( Form ):
	last_name = forms.CharField( label = _('Last Name') )
	gender = forms.ChoiceField( choices = ((0, _('Men')), (1, _('Women'))) )
	date_of_birth = forms.DateField( label = _('Date of Birth') )
	
	def __init__(self, *args, **kwargs):
		from_post = kwargs.pop('from_post', False)
		has_matches = kwargs.pop('has_matches', False)
		super().__init__(*args, **kwargs)
			
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' )]
		if from_post:
			button_args.append( Submit( 'new-submit', _('Not Found - Create New License Holder'), css_class = 'btn btn-success' ) )
		button_args.append( CancelButton() )
		
		self.helper.layout = Layout(
			Row(
				Field('last_name', size=44),
				Field('gender'),
				Field('date_of_birth'),
			),
			Row( *button_args ),
		)

@access_validation()
def ParticipantNotFound( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	has_matches = False
	matches = []
	
	key = 'participant_not_found'
	def set_form_fields( last_name, gender, date_of_birth ):
		request.session[key] = {'last_name':last_name, 'gender':gender, 'date_of_birth':date_of_birth.strftime('%Y-%m-%d')}
	
	def get_form_fields():
		fields = request.session.get(key, {})
		try:
			fields['date_of_birth'] = datetime.date( *[int(f) for f in fields['date_of_birth'].split('-')] )
		except KeyError:
			pass
		return fields
	
	if request.method == 'POST':
	
		form = ParticipantNotFoundForm( request.POST, from_post=True )
		if form.is_valid():
			last_name = form.cleaned_data['last_name']
			last_name = last_name[:1].upper() + last_name[1:]
			gender = int(form.cleaned_data['gender'])
			date_of_birth = form.cleaned_data['date_of_birth']
			set_form_fields( last_name, gender, date_of_birth )
			
			if 'search-submit' in request.POST:
				matches = LicenseHolder.objects.filter( gender=gender, date_of_birth=date_of_birth, search_text__startswith=utils.get_search_text(last_name) )
				secondary_matches = LicenseHolder.objects.filter( search_text__icontains=utils.get_search_text(last_name) ).exclude( pk__in=matches.values_list('pk',flat=True) )
				has_matches = matches.exists() or secondary_matches.exists()
				if has_matches:
					form = ParticipantNotFoundForm( initial={'last_name':last_name, 'gender':gender, 'date_of_birth':date_of_birth}, has_matches=has_matches, from_post=True )
					return render( request, 'participant_not_found.html', locals() )
		
			if 'new-submit' in request.POST or not has_matches:
				license_holder = LicenseHolder( last_name=last_name, first_name=last_name[:1], gender=gender, date_of_birth=date_of_birth )
				license_holder.save()
				participant = Participant( competition=competition, license_holder=license_holder )
				participant.save()
				return HttpResponseRedirect( getContext(request,'cancelUrl') +
					'ParticipantEdit/{}/'.format(participant.id) +
					'LicenseHolderEdit/{}/'.format(license_holder.id)
				)
	else:
		form = ParticipantNotFoundForm( initial=get_form_fields() )

	return render( request, 'participant_not_found.html', locals() )

@access_validation()
def ParticipantLicenseHolderFound( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	return HttpResponseRedirect( getContext(request,'pop2Url') +
		'ParticipantAddToCompetition/{}/{}/'.format(competition.id, license_holder.id)
	)
	
