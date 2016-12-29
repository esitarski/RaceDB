import datetime
import operator
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from views_common import *
from models import *

from views import license_holders_from_search_text

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
			Row( HTML('<img src="{}"/>'.format(static('images/RaceDB_small.png'))), HTML('&nbsp;'*4),
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
	competitions = Competition.objects.all()

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
