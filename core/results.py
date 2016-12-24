from views_common import *
import datetime
from django.utils.translation import ugettext_lazy as _
from views import license_holders_from_search_text

def ResultsMassStart( request, eventId ):
	time_stamp = datetime.datetime.now()
	event = get_object_or_404( EventMassStart, pk=eventId )
	return render( request, 'results_mass_start_list.html', locals() )

def ResultsMassStartCategory( request, eventId, categoryId ):
	time_stamp = datetime.datetime.now()
	event = get_object_or_404( EventMassStart, pk=eventId )
	category = get_object_or_404( Category, pk=categoryId )
	results = event.get_results().filter( participant__category=category ).order_by('category_rank')
	num_nationalities = results.exclude(participant__license_holder__nation_code='').values('participant__license_holder__nation_code').distinct().count()
	num_starters = results.exclude( status=Result.cDNS ).count()
	return render( request, 'results_mass_start_category_list.html', locals() )

def ResultsMassStartDashboard( request, eventId, participantId, categoryId = None ):
	event = get_object_or_404( EventMassStart, pk=eventId )
	participant = get_object_or_404( Participant, participantId )
	category = get_object_or_404( Category, categoryId ) if categoryId else None
	
	
def ResultsTT( request, eventId ):
	time_stamp = datetime.datetime.now()
	event = get_object_or_404( EventMassStart, pk=eventId )
	return render( request, 'results_tt_list.html', locals() )

