import datetime
import operator
from collections import defaultdict
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from views_common import *
from models import *

from views import license_holders_from_search_text
from results import get_payload_for_result

ItemsPerPage = 25

def comptitions_with_results():
	non_empty = []
	non_empty.extend( ResultMassStart.objects.all().values_list('event__competition__pk',flat=True).distinct() )
	non_empty.extend( ResultTT.objects.all().values_list('event__competition__pk',flat=True).distinct() )	
	return Competition.objects.filter(pk__in=non_empty)

@autostrip
class CompetitionSearchForm( Form ):
	name_text = forms.CharField( required=False, label = _('Name Text') )
	year = forms.ChoiceField( required=False, label=_('Year') )
	
	def __init__(self, *args, **kwargs):
		super(CompetitionSearchForm, self).__init__(*args, **kwargs)
		
		year_cur = datetime.datetime.now().year
		competition =comptitions_with_results().order_by('start_date').first()
		year_min = competition.start_date.year if competition else year_cur
		self.fields['year'].choices =  [(-1, '----')] + [(y, u'{:04d}'.format(y)) for y in xrange(year_cur, year_min-1, -1)]
			
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( HTML('<span style="font-size: 180%;">'), HTML(_('Search Competitions')), HTML("</span>&nbsp;&nbsp;"),
				Field('name_text', size=20, autofocus=True ), HTML('&nbsp;'*4), Field('year'), HTML('&nbsp;'*4), button_args[0]),
		)

def getPaginator( request, page_key, items ):
	paginator = Paginator( items, ItemsPerPage )
	page = request.GET.get('page',None) or request.session.get(page_key,None)
	try:
		items = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		page = 1
		items = paginator.page(page)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		page = paginator.num_pages
		items = paginator.page(page)
	request.session[page_key] = page
	return items, paginator
	
def SearchCompetitions( request ):
	key = 'hub_competitions'
	page_key = key + '_page'

	competition_filter = request.session.get(key, {})
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = CompetitionSearchForm( request.POST )
		if form.is_valid():
			competition_filter = form.cleaned_data
			request.session[key] = competition_filter
			request.session[page_key] = None
	else:
		form = CompetitionSearchForm( initial = competition_filter )
	
	competitions = comptitions_with_results()
	
	if competition_filter.get('name_text','').strip():
		name_text = competition_filter.get('name_text','').strip()
		for n in name_text.split():
			competitions = competitions.filter( name__icontains=n )
	competitions = competitions.order_by('-start_date')
	
	competitions, paginator = getPaginator( request, page_key, competitions )
	exclude_breadcrumbs = True
	return render( request, 'hub_competitions_list.html', locals() )

def CompetitionResults( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	events = competition.get_events()
	events.sort( key=operator.attrgetter('date_time') )
	
	event_day = set()
	for e in events:
		event_day.add( timezone.localtime(e.date_time).strftime('%Y-%m-%d') )
		
	event_days = sorted( event_day )
	get_day = {d:i for i, d in enumerate(event_days)}
	
	category_results = defaultdict(lambda: [[] for i in xrange(len(event_days))])
	for e in events:
		day = get_day[timezone.localtime(e.date_time).strftime('%Y-%m-%d')]
		for w in e.get_wave_set().all():
			for c in set( rr.participant.category for rr in w.get_results().select_related('participant','participant__category') ):
				category_results[c][day].append( (e, w) )
				
	category_results = [(k,v) for k,v in category_results.iteritems()]
	category_results.sort( key=lambda p:(p[0].gender, p[0].sequence) )
	
	exclude_breadcrumbs = True
	return render( request, 'hub_events_list.html', locals() )

def CategoryResults( request, eventId, eventType, categoryId ):
	event = get_object_or_404( (EventMassStart,EventTT)[int(eventType)], pk=eventId )
	category = get_object_or_404( Category, pk=categoryId )
	wave = event.get_wave_for_category( category )
	
	if wave.rank_categories_together:
		results = wave.get_results()
		cat_name = wave.name
	else:
		results = event.get_results().filter( participant__category=category ).order_by('status','category_rank')
		cat_name = category.code_gender
	
	num_nationalities = results.exclude(participant__license_holder__nation_code='').values('participant__license_holder__nation_code').distinct().count()
	num_starters = results.exclude( status=Result.cDNS ).count()
	time_stamp = datetime.datetime.now()

	exclude_breadcrumbs = True
	return render( request, 'hub_results_list.html', locals() )

def LicenseHolderResults( request, licenseHolderId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	exclude_breadcrumbs = True
	return render( request, 'hub_license_holder_results.html', locals() )

def ResultAnalysis( request, eventId, eventType, resultId ):
	event = get_object_or_404( (EventMassStart,EventTT)[int(eventType)], pk=eventId )
	result = get_object_or_404( event.get_result_class(), pk=resultId )
	payload = get_payload_for_result( result )
	exclude_breadcrumbs = True
	hub_mode = True
	return render( request, 'RiderDashboard.html', locals() )
	
#---------------------------------------------------------------------------------------------------

@autostrip
class LicenseHolderSearchForm( Form ):
	last_name = forms.CharField( required=False, label = _('Last Name') )
	first_name = forms.CharField( required=False, label = _('First Name') )
	
	def __init__(self, *args, **kwargs):
		super(LicenseHolderSearchForm, self).__init__(*args, **kwargs)

		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( HTML('<span style="font-size: 180%;">'), HTML(_('Search Athletes')), HTML("</span>&nbsp;&nbsp;"),
				Field('last_name', size=20, autofocus=True ), HTML('&nbsp;'*4),
				Field('first_name', size=20 ), HTML('&nbsp;'*4),
				button_args[0]),
		)

def SearchLicenseHolders( request ):
	key = 'hub_license_holders'
	page_key = key + '_page'

	license_holder_filter = request.session.get(key, {})
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = LicenseHolderSearchForm( request.POST )
		if form.is_valid():
			license_holder_filter = form.cleaned_data
			request.session[key] = license_holder_filter
			request.session[page_key] = None
	else:
		form = LicenseHolderSearchForm( initial = license_holder_filter )
	
	search_fields = []
	if license_holder_filter.get('last_name','').strip():
		search_fields.append( license_holder_filter.get('last_name','').strip() )
	if search_fields and license_holder_filter.get('first_name','').strip():
		search_fields.append( license_holder_filter.get('first_name','').strip() )
		
	if search_fields:
		license_holders = LicenseHolder.objects.filter( search_text__startswith=utils.get_search_text(search_fields) )
	else:
		license_holders = LicenseHolder.objects.filter( license_code__isnull=True )
	
	license_holders, paginator = getPaginator( request, page_key, license_holders )
	exclude_breadcrumbs = True
	return render( request, 'hub_license_holders_list.html', locals() )


