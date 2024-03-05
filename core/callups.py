from django.utils.translation import gettext_lazy as _

from .views_common import *
from .series_results import extract_event_results, get_callups_for_wave

@access_validation()
def Callups( request, eventId, eventType, seriesId ):
	event = get_object_or_404( (EventMassStart, EventTT)[int(eventType)], pk=eventId )
	series = get_object_or_404( Series, pk=seriesId )
	competition = event.competition
	
	# Get all related categories for this Event.
	categories = set()
	for c in event.get_categories():
		if c not in categories:
			categories |= series.get_related_categories( c )
	
	# Get all license holders for this Event.
	license_holders = set( p.license_holder for p in event.get_participants() )
	
	# Get event results for all the categories.  This only hits the database once.
	eventResultsAll = []
	for sce in series.seriescompetitionevent_set.all():
		if sce.event.date_time < event.date_time:
			eventResultsAll.extend( extract_event_results(sce, categories, license_holders) )
	
	wave_callups = []
	for w in event.get_wave_set().all():
		callups = get_callups_for_wave( series, w, eventResultsAll )
		
		# Format the points colunms nicely.
		for cg, p_points in callups:
			p_points[:] = [(lh, fp if not fp.startswith('0') else '')
				for lh, fp in zip(
					[lh for lh, p in p_points],
					format_column_float(p for lh, p in p_points)
				)
			]
		
		if callups:
			wave_callups.append( (w, 12//(len(callups) if callups else 1), callups) )
		
	return render( request, 'callups.html', locals() )
