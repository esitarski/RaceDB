import re
import datetime
import operator
from collections import defaultdict
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from views_common import *
from models import *

from views import license_holders_from_search_text
from results import get_payload_for_result

ItemsPerPage = 25

def competitions_with_results( competitions=None ):
	if competitions is None:
		competitions = Competition.objects.all()		
	return competitions.filter(
		Q(pk__in=ResultMassStart.objects.values_list('event__competition__pk',flat=True).distinct()) |
		Q(pk__in=ResultTT.objects.values_list('event__competition__pk',flat=True).distinct())
	).distinct()

@autostrip
class CompetitionSearchForm( Form ):
	year = forms.ChoiceField( required=False, label=_('Year') )
	discipline = forms.ChoiceField( required=False, label=('Discipline') )
	name_text = forms.CharField( required=False, label = _('Name Text') )
	
	def __init__(self, *args, **kwargs):
		super(CompetitionSearchForm, self).__init__(*args, **kwargs)
		
		competitions = competitions_with_results()
		
		year_cur = datetime.datetime.now().year
		
		competition = competitions.order_by('start_date').first()
		year_min = competition.start_date.year if competition else year_cur
		competition = competitions.order_by('-start_date').first()
		year_max = competition.start_date.year if competition else year_cur
		self.fields['year'].choices =  [(-1, '----')] + [(y, u'{:04d}'.format(y)) for y in xrange(year_max, year_min-1, -1)]
		
		disciplines = Discipline.objects.filter( pk__in=competitions.values_list('discipline', flat=True).distinct() )
		self.fields['discipline'].choices =  [(-1, '----')] + [(d.pk, d.name) for d in disciplines]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class='btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row(
				HTML('<span style="font-size: 180%;">'),
				HTML(_('Search Competitions')), HTML("</span>&nbsp;&nbsp;"),
				Field('year'), HTML('&nbsp;'*2),
				Field('discipline'), HTML('&nbsp;'*2),
				Field('name_text', size=20, autofocus=True ), HTML('&nbsp;'*2),
				Field( button_args[0] ),
			),
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
	
	competitions = Competition.objects.all()
	
	search_year = int( competition_filter.get('year',-1) )
	if search_year > 0:
		date_min = datetime.date( search_year, 1, 1 )
		date_max = datetime.date( search_year+1, 1, 1 ) - datetime.timedelta(days=1)
		competitions = competitions.filter( start_date__range=(date_min, date_max) )
	
	dpk = int( competition_filter.get('discipline',-1) )
	if dpk >= 0:
		competitions = competitions.filter( discipline__pk=dpk )
	
	if competition_filter.get('name_text','').strip():
		name_text = competition_filter.get('name_text','').strip()
		for n in name_text.split():
			competitions = competitions.filter( name__icontains=n )
	
	competitions = competitions_with_results( competitions ).order_by('-start_date')
	
	competitions, paginator = getPaginator( request, page_key, competitions )
	exclude_breadcrumbs = True
	return render( request, 'hub_competitions_list.html', locals() )

def CompetitionResults( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	events = competition.get_events()
	events.sort( key=operator.attrgetter('date_time') )
	
	event_days = sorted( set( timezone.localtime(e.date_time).strftime('%Y-%m-%d') for e in events ) )
	get_day = {d:i for i, d in enumerate(event_days)}
	
	category_results = defaultdict(lambda: [[] for i in xrange(len(event_days))])
	for e in events:
		day = get_day[timezone.localtime(e.date_time).strftime('%Y-%m-%d')]
		for w in e.get_wave_set().all():
			for c in Category.objects.filter( pk__in=w.get_results().values_list('participant__category__pk',flat=True).distinct() ):
				category_results[c][day].append( (e, w) )

	category_results = [(k,v) for k,v in category_results.iteritems()]
	category_results.sort( key=lambda p:(p[0].gender, p[0].sequence) )
	
	gender_category_results = [[],[],[]]
	for v in category_results:
		gender_category_results[v[0].gender].append( v )
	gender_category_results = [(gr[0][0], gr) for gr in gender_category_results if gr]
	col_gender = 12 // (len(gender_category_results) if gender_category_results else 1)
	
	#--------------------------------------------------------------------
	custom_category_results = [[] for d in event_days]
	for e in events:
		day = get_day[timezone.localtime(e.date_time).strftime('%Y-%m-%d')]
		custom_categories = list(e.get_custom_categories())
		if not custom_categories:
			continue
		if not custom_category_results[day] or custom_category_results[day][-1] != e:
			custom_category_results[day].append( (e, []) )
		for cc in custom_categories:
			custom_category_results[day][-1][1].append( cc )
	
	custom_category_results = [ccr for ccr in custom_category_results if ccr]
	if custom_category_results:
		row_max = max( len(ccr) for ccr in custom_category_results )
		col_max = len( ccr )
		ccr_table = [ [(None,[]) for r in xrange(col_max)] for c in xrange(row_max) ]
		for i, ccr in enumerate(custom_category_results):
			for j, ecc in enumerate(ccr):
				ccr_table[j][i] = ecc
		ccr_header = [timezone.localtime(ccr[0][0].date_time).strftime('%Y-%m-%d') for ccr in custom_category_results]
	else:
		ccr_table = ccr_header = []
		
	exclude_breadcrumbs = True
	return render( request, 'hub_events_list.html', locals() )

def CategoryResults( request, eventId, eventType, categoryId ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart,EventTT)[eventType], pk=eventId )
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
	time_stamp = timezone.datetime.now()

	payload = get_payload_for_result( results.first() )
	exclude_breadcrumbs = True
	hub_mode = True
	is_timetrial = (eventType == 1)
	show_category = wave.rank_categories_together
	return render( request, 'hub_results_list.html', locals() )

def CustomCategoryResults( request, eventId, eventType, customCategoryId ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart, EventTT)[eventType], pk=eventId )
	CCC = event.get_custom_category_class()
	custom_category = category = get_object_or_404( CCC, pk=customCategoryId )
	
	results = custom_category.get_results()
	num_nationalities = len(set(rr.participant.license_holder.nation_code for rr in results if rr.participant.license_holder.nation_code))
	num_starters = sum( 1 for rr in results if rr.status != Result.cDNS )
	time_stamp = timezone.datetime.now()

	payload = get_payload_for_result( results[0] ) if results else {}
	exclude_breadcrumbs = True
	hub_mode = True
	is_timetrial = (eventType == 1)
	show_category = True
	return render( request, 'hub_results_list.html', locals() )

def LicenseHolderResults( request, licenseHolderId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	exclude_breadcrumbs = True
	return render( request, 'hub_license_holder_results.html', locals() )

def ResultAnalysis( request, eventId, eventType, resultId ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart,EventTT)[eventType], pk=eventId )
	is_timetrial = (event.event_type == 1)
	result = get_object_or_404( event.get_result_class(), pk=resultId )
	license_holder = result.participant.license_holder
	payload = get_payload_for_result( result )
	exclude_breadcrumbs = True
	hub_mode = True
	is_timetrial = (eventType == 1)
	return render( request, 'RiderDashboard.html', locals() )
	
#---------------------------------------------------------------------------------------------------

@autostrip
class LicenseHolderSearchForm( Form ):
	search_text = forms.CharField( required=False, label=_('Text') )
	search_type = forms.ChoiceField( required=False, choices = ((0,_('Name (Last, First)')),(1,_('License')),(2,_('UCIID'))),
		label=_('Search by') ) 
	
	def __init__(self, *args, **kwargs):
		super(LicenseHolderSearchForm, self).__init__(*args, **kwargs)

		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( HTML('<span style="font-size: 180%; vertical-align:middle;">'), HTML(_('Search Athletes')), HTML("</span>&nbsp;&nbsp;"),
				Field('search_text', size=20, autofocus=True  ), HTML('&nbsp;'*4),
				Field('search_type'), HTML('&nbsp;'*4),
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
	
	search_text = license_holder_filter.get('search_text','').strip()
	search_type = int(license_holder_filter.get('search_type',0))
	
	if search_text:
		if search_type == 0:
			search_fields = search_text.split(',')[:2]
			st = utils.get_search_text([f.strip() for f in search_fields])[:-1]
			license_holders = LicenseHolder.objects.filter( search_text__startswith=st )
		elif search_type == 1:
			license_holders = LicenseHolder.objects.filter( license_code=search_text.upper() )
		elif search_type == 2:
			license_holders = LicenseHolder.objects.filter( uci_code=search_text.replace(' ', '') )
		
		# Only return license holders with results.
		license_holders = license_holders.filter(
			Q(pk__in=ResultMassStart.objects.all().values_list('participant__license_holder',flat=True).distinct()) |
			Q(pk__in=ResultTT.objects.all().values_list('participant__license_holder',flat=True).distinct())
		)
	else:
		license_holders = LicenseHolder.objects.none()
	
	license_holders, paginator = getPaginator( request, page_key, license_holders )
	exclude_breadcrumbs = True
	return render( request, 'hub_license_holders_list.html', locals() )

#-------------------------------------------------------------------------

def SeriesList( request ):
	page_key = 'hub_series'
	series = Series.objects.all()
	if not request.user.is_superuser:
		series = series.exclude( name__startswith='_' )
	
	paginator = None
	if series.count() > ItemsPerPage:
		series, paginator = getPaginator( request, page_key, series )
		series_exists = True
	else:
		series_exists = series.exists()
		
	exclude_breadcrumbs = True
	return render( request, 'hub_series_list.html', locals() )

def SeriesCategories( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	
	gender_categories = [[],[],[]]
	for c in series.get_categories():
		gender_categories[c.gender].append( c )
	gender_categories = [(gc[0], gc) for gc in gender_categories if gc]
	col_gender = 12 // (len(gender_categories) if gender_categories else 1)
	
	exclude_breadcrumbs = True
	return render( request, 'hub_series_categories_list.html', locals() )

#------------------------------------------------------------------------------------

import series_results

def SeriesCategoryResults( request, seriesId, categoryId ):
	series = get_object_or_404( Series, pk=seriesId )
	category = get_object_or_404( Category, pk=categoryId )
	
	results, events = series_results.get_results_for_category( series, category )
	group_categories = series.get_group_related_categories( category )
	
	# Create data for a Sankey diagram.
	sankeyMax = 1000
	total_values = [totalValue for lh, team, totalValue, gap, event_results in results][:sankeyMax]
	if series.ranking_criteria == 1:
		total_values = format_column_time( total_values )
	else:
		total_values = format_column_float( total_values )
	
	json_data = []
	json_format = formatTime if series.ranking_criteria == 1 else lambda v: '{:.2f}'.format(v)
	team_map = {}
	team_count = 0
	team_total = defaultdict( int )
	team_arc = defaultdict( int )
	max_team_len = 15
	for rank, (lh, team, totalValue, gap, event_results) in enumerate(results[:sankeyMax], 1):
		rider_name = lh.full_name()
		node_name = u'{:2d}. {} ({})'.format( rank, rider_name, total_values[rank-1] )
		for er in event_results:
			if not er or er.ignored:
				continue
			event_name = u'{}-{}: {}'.format( er.event.competition.name, er.event.name, er.event.date_time.strftime('%Y-%m-%d') )
			json_data.append( [
				event_name,
				node_name,
				{'v':er.value_for_rank, 'f':json_format(er.value_for_rank)},
				None if True else u'{} \u2192 {}, {}{} \u2192 {}'.format(
					event_name,
					re.sub(r'.00$|0$', '', json_format(er.value_for_rank)), er.rank_text, u'\u00A0\u2191' if er.upgraded else u'',
					rider_name,
				),
			] )
			if series.ranking_criteria != 1:
				try:
					team_name = team_map[node_name]
				except KeyError:
					if not team or 'independent' in team:
						team_count += 1
						team_name = u'Ind {}'.format(team_count)
					else:
						team_name = team
					if len(team_name) > max_team_len:
						team_name = team_name[:max_team_len].strip() + u'...'
					team_map[node_name] = team_name
				
				team_arc[(node_name, team_name)] += er.value_for_rank
				team_total[team_name] += er.value_for_rank

	tt = [(n,v) for n,v in team_total.iteritems()]
	team_total = { n:f for (n,v), f in zip(tt, format_column_float( [t[1] for t in tt] )) }
		
	for node_name, team_name, value in sorted( ((n, t, v) for (n,t), v in team_arc.iteritems()), key=operator.itemgetter(2), reverse=True ):
		json_data.append( [
			node_name,
			u'{} ({})'.format(team_name, team_total[team_name]),
			{'v':value, 'f':json_format(value)},
			None,
		] )
	
	# Format the results based on the ranking criteria.
	total_values = []
	gaps = []
	event_results_values = defaultdict( list )
	
	has_upgrades, has_ignored = False, False
	for lh, team, totalValue, gap, event_results in results:
		total_values.append( totalValue )
		gaps.append( gap )
		for i, er in enumerate(event_results):
			if er:
				event_results_values[i].append( er.value_for_rank )
				has_upgrades |= er.upgraded
				has_ignored  |= er.ignored
			else:
				event_results_values[i].append( None )
	
	if series.ranking_criteria == 1:
		total_values = format_column_time( total_values )
		gaps = [(v or u'') for v in format_column_gap(gaps)]
		for erv in event_results_values.itervalues():
			erv[:] = format_column_time( erv )
	else:
		total_values = format_column_float( total_values )
		gaps = format_column_float( gaps )
		for erv in event_results_values.itervalues():
			erv[:] = format_column_float( erv )

	for row, r in enumerate(results):
		# Skip lh and team.
		r[2] = total_values[row]
		r[3] = gaps[row]
		for i, er in enumerate(r[4]):
			if event_results_values[i][row] is not None:
				er.value_for_rank = event_results_values[i][row]

	points_structure_summary = defaultdict( list )
	if series.ranking_criteria == 0:
		for ce in series.seriescompetitionevent_set.all():
			points_structure_summary[ce.points_structure].append( ce.event )
		points_structure_summary = [(k, v) for k, v in points_structure_summary.iteritems()]
		points_structure_summary.sort( key=lambda v: v[0].sequence )
				
	time_stamp = timezone.datetime.now()
	exclude_breadcrumbs = True
	return render( request, 'hub_series_results.html', locals() )
