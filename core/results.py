import datetime
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .views_common import *
from .views import license_holders_from_search_text

def get_payload_for_result( has_results, result_list, cat_name, cat_type, result=None ):
	if not result_list or not has_results:
		return {}

	result = result or result_list[0]
	event = result.event
	competition = event.competition
	
	payload = {}
	payload['bib'] = result.participant.bib
	payload['raceName'] = '{} - {} ({})'.format( competition.title, event.name, competition.discipline.name )
	payload['raceScheduledStart'] = timezone.localtime(event.date_time).strftime( '%Y-%m-%d %H:%M' )
	payload['winAndOut'] = getattr(event, 'win_and_out', False)
	payload['isTimeTrial'] = (event.event_type == 1)
	payload['primes'] = None
	payload['raceIsRunning'] = False
	payload["raceIsUnstarted"] = False
	payload['infoFields'] = ['LastName', 'FirstName', 'Team', 'License', 'UCI ID', 'NatCode', 'City', 'StateProv']
	payload['has_results'] = has_results
	
	data = {}
	race_times_all = []
	pos = []
	raceDistance = None
	distance = None
	firstLapDistance = None
	lapDistance = None
	
	units_conversion = 1.0 if competition.distance_unit == 0 else 0.621371
	speed_unit = 'km/h' if competition.distance_unit == 0 else 'mph'
	distance_unit = 'km' if competition.distance_unit == 0 else 'miles'
	
	for rr in result_list:
		p = rr.participant
		h = p.license_holder
		
		info = rr.get_info_by_lap()
		race_times, lap_kmh, lap_km = info['race_times'], info['lap_kmh'], info['lap_km']
		d = {
			'LastName': h.last_name,
			'FirstName': h.first_name,
			'Team':		p.team.name if p.team else '',
			'License':	h.license_code_trunc,
			'UCIID':	h.uci_id,
			'NatCode':	h.nation_code,
			'Gender':	('Men','Women')[h.gender],
			'City':		h.city,
			'StateProv':h.state_prov,
			
			'raceTimes': race_times,
			'interp':	[0] * len(race_times),
			'lastTime': race_times[-1] if race_times else 0.0,
			'lastTimeOrig': race_times[-1] if race_times else 0.0,
			'status':	rr.status_text,
		}
		if rr.ave_kmh:
			d['speed'] = '{:.2f} {}'.format(rr.ave_kmh*units_conversion, speed_unit)
			# Get raceDistance from leader.
			if raceDistance is None and race_times:
				raceDistance = units_conversion * rr.ave_kmh * (race_times[-1] - race_times[0])/(60.0*60.0)
		
		if lap_kmh:
			d['lapSpeeds'] = [s*units_conversion for s in lap_kmh]
			if firstLapDistance is None:
				try:
					firstLapDistance = units_conversion * lap_km[0]
					lapDistance = units_conversion * lap_km[1]
				except Exception:
					pass
				
		data[p.bib] = d
		pos.append( p.bib )
		race_times_all.append( race_times )
		
	gapValue = []
	winner_finish = race_times_all[0][-1]
	winner_laps = max(len(race_times_all[0]), 1)
	for rt in race_times_all:
		if len(race_times_all[0]) != len(rt):
			gapValue.append( len(rt) - winner_laps )
		else:
			gapValue.append( rt[-1] - winner_finish )
	
	catDetails = {
		'name':		cat_name,
		'catType':	cat_type,
		'pos':		pos,
		'gapValue':	gapValue,
		'laps':		winner_laps,
		'startOffset': 0,
	}
	if raceDistance:
		catDetails['raceDistance'] = raceDistance
	if firstLapDistance and firstLapDistance != lapDistance:
		catDetails['firstLapDistance'] = firstLapDistance
	if lapDistance:
		catDetails['lapDistance'] = lapDistance
	payload['catDetails'] = [catDetails]
	payload['data'] = data
	
	return payload

'''
def Results( request, eventId, eventType ):
	time_stamp = datetime.datetime.now()
	event = get_object_or_404( (EventMassStart, EventTT)[int(eventType)], pk=eventId )
	return render( request, 'results_list.html', locals() )

def ResultsCategory( request, eventId, eventType, categoryId ):
	event = get_object_or_404( (EventMassStart, EventTT)[int(eventType)], pk=eventId )
	category = get_object_or_404( Category, pk=categoryId )
	wave = event.get_wave_for_category( category )
	if wave.rank_categories_together:
		results = wave.get_results()
	else:
		results = event.get_results().filter( participant__category=category ).order_by('status','category_rank')
	num_nationalities = results.exclude(participant__license_holder__nation_code='').values('participant__license_holder__nation_code').distinct().count()
	num_starters = results.exclude( status=Result.cDNS ).count()
	time_stamp = datetime.datetime.now()
	return render( request, 'results_category_list.html', locals() )

def ResultAnaysis( request, eventId, eventType, resultId ):
	event = get_object_or_404( (EventMassStart, EventTT)[int(eventType)], pk=eventId )
	result = get_object_or_404( event.get_result_class(), pk=resultId )
	payload = get_payload_for_result( result )
	return render( request, 'RiderDashboard.html', locals() )
'''
