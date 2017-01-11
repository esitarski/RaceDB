import operator
from collections import defaultdict

from views_common import *
from series_results import get_callups_for_wave
from django.utils.translation import ugettext_lazy as _

@access_validation()
def Callups( request, eventId, eventType, seriesId ):
	event = get_object_or_404( (EventMassStart, EventTT)[int(eventType)], pk=eventId )
	series = get_object_or_404( Series, pk=seriesId )
	competition = event.competition
	
	wave_callups = []
	for w in event.get_wave_set().all():
		callups = get_callups_for_wave( series, w )
		
		# Format the points colun nicely.
		for cg, p_points in callups:
			p_points[:] = [(lh, fp if not fp.startswith('0') else u'')
				for lh, fp in zip(
					[lh for lh, p in p_points],
					format_column_float(p for lh, p in p_points)
				)
			]
		
		if callups:
			wave_callups.append( (w, 12//(len(callups) if callups else 1), callups) )
		
	return render( request, 'callups.html', locals() )
