
import utils
from collections import defaultdict
from models import *

def participation_data( year=None ):
	competitions = Competition.objects.all()
	if year is not None:
		competitions = competitions.filter( start_date__year = year )
	
	data = []
	license_holders_count = defaultdict( int )
	license_holders_men_count = defaultdict( int )
	license_holders_women_count = defaultdict( int )
	age_count = defaultdict( int )
	age_men_count = defaultdict( int )
	age_women_count = defaultdict( int )
	
	for competition in competitions.order_by( 'start_date' ):
		if not competition.has_participants():
			continue
		
		competition_data = {
			'name': competition.name,
			'start_date': competition.start_date.strftime('%Y-%m-%d'),
			'events': [],
			'men': 0,
			'women': 0,
			'total': 0,
		}
		for event in competition.get_events():
			if not event.has_participants():
				continue
			participant_data = []
			for participant in event.get_participants():
				age = event.date_time.year - participant.license_holder.date_of_birth.year
				participant_data.append( {
					'gender':	participant.license_holder.gender,
					'age':		age,
				} )
				license_holders_count[participant.license_holder] += 1
				age_count[age] += 1
				if participant.license_holder.gender == 0:
					license_holders_men_count[participant.license_holder] += 1
					age_men_count[age] += 1
				else:
					license_holders_women_count[participant.license_holder] += 1
					age_women_count[age] += 1
			
			event_data = {
				'name':event.name,
				'participants':participant_data,
				'men': sum(1 for p in participant_data if p['gender'] == 0),
				'women': sum(1 for p in participant_data if p['gender'] == 1),
			}
			event_data['total'] = event_data['men'] + event_data['women']
			competition_data['men'] += event_data['men']
			competition_data['women'] += event_data['women']
			competition_data['events'].append( event_data )
		
		competition_data['total'] = competition_data['men'] + competition_data['women']
		data.append( competition_data )
	
	def get_expected_age( ac ):
		most_frequent = max( v for v in ac.itervalues() )
		for a, c in ac.iteritems():
			if c == most_frequent:
				return a
		return None
	
	payload = {
		'participants_total': sum(c['total'] for c in data),
		'participants_men_total': sum(c['men'] for c in data),
		'participants_women_total': sum(c['women'] for c in data),
		'license_holders_total': len(license_holders_count),
		'license_holders_men_total': len(license_holders_men_count),
		'license_holders_women_total': len(license_holders_women_count),
		'events_average': sum(v for v in license_holders_count.itervalues()) / float(len(license_holders_count)),
		'events_men_average': sum(v for v in license_holders_men_count.itervalues()) / float(len(license_holders_men_count)),
		'events_women_average': sum(v for v in license_holders_women_count.itervalues()) / float(len(license_holders_women_count)),
		'expected_age': get_expected_age(age_count),
		'expected_men_age': get_expected_age(age_men_count),
		'expected_women_age': get_expected_age(age_women_count),
		'competitions': data,
	}
	return payload
