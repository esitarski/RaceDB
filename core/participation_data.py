
import datetime
import utils
from collections import defaultdict
from models import *

def participation_data( start_date=None, end_date=None, discipline=None, race_class=None, organizers=None ):
	discipline = int(discipline or -1)
	race_class = int(race_class or -1)

	competitions = Competition.objects.all()
	if start_date is not None:
		competitions = competitions.filter( start_date__gte = start_date )
	if end_date is not None:
		competitions = competitions.filter( start_date__lte = end_date )
	if discipline > 0:
		competitions = competitions.filter( discipline__pk = discipline )
	if race_class > 0:
		competitions = competitions.filter( race_class__pk = race_class )
	if organizers:
		competitions = competitions.filter( organizer__in = organizers )
	
	competitions = competitions.order_by( 'start_date' )
	
	license_holders_event_errors = set()
	
	data = []
	license_holders_attendance_total = defaultdict( int )
	license_holders_men_total = defaultdict( int )
	license_holders_women_total = defaultdict( int )
	
	category_total_overall = defaultdict( int )
	category_competition_total = defaultdict( lambda: defaultdict(int) )
	event_competition_participant_total = defaultdict( lambda: defaultdict(int) )
	competition_attendee_total = defaultdict( int )
	competition_participant_total = defaultdict( int )
	
	competition_category_event = defaultdict( dict )
	
	age_increment = 5
	age_range_license_holders = [set() for i in xrange(0, 120, age_increment)]
	age_range_attendee_count = [0 for i in xrange(0, 120, age_increment)]
	age_range_men_license_holders = [set() for i in xrange(0, 120, age_increment)]
	age_range_men_attendee_count = [0 for i in xrange(0, 120, age_increment)]
	age_range_women_license_holders = [set() for i in xrange(0, 120, age_increment)]
	age_range_women_attendee_count = [0 for i in xrange(0, 120, age_increment)]
	license_holders_set = set()
	
	profile_year = 0
	participant_total = 0
	competitions_total, events_total = 0, 0
	
	def fix_age( age ):
		return max(min(age, 119), 0)
	
	for competition in competitions:
		if not competition.has_participants():
			continue
		
		competitions_total += 1
		profile_year = max( profile_year, competition.start_date.year )
		
		competition_data = {
			'name': competition.name,
			'start_date': competition.start_date.strftime('%Y-%m-%d'),
			'events': [],
			'attendees_men': 0,
			'attendees_women': 0,
			'attendees_total': 0,
			'participants_men': 0,
			'participants_women': 0,
			'participant_total': 0,
		}
		for event in competition.get_events():
			if not event.has_participants():
				continue
				
			events_total += 1
			
			attendee_data = []
			participant_data = []
			event_license_holders = set()
			for participant in event.get_participants():
				
				# Participation.
				license_holder = participant.license_holder
				age = event.date_time.year - license_holder.date_of_birth.year
				if not (7 < age < 100):
					license_holders_event_errors.add( (license_holder, event) )
				age = fix_age( age )
				
				event_competition_participant_total[competition][event] += 1
				category_name = participant.category.code_gender if participant.category else unicode(_('Unknown'))
				category_total_overall[category_name] += 1
				category_competition_total[competition][category_name] += 1
				competition_category_event[competition][category_name] = event.name
				competition_participant_total[competition] += 1
				participant_total += 1
				participant_data.append( [license_holder.gender, age] )
				
				if license_holder in event_license_holders:
					continue
				
				# Attendance: definition: a LicenseHolder that attends a Competition
				event_license_holders.add( license_holder )
				
				attendee_data.append( [license_holder.gender, age] )
				license_holders_set.add( license_holder )
				license_holders_attendance_total[license_holder] += 1
				
				bucket = age // age_increment
				
				age_range_license_holders[bucket].add( license_holder )
				age_range_attendee_count[bucket] += 1
				
				competition_attendee_total[competition] += 1
				
				if license_holder.gender == 0:
					license_holders_men_total[license_holder] += 1
					age_range_men_license_holders[bucket].add( license_holder )
					age_range_men_attendee_count[bucket] += 1
				else:
					license_holders_women_total[license_holder] += 1
					age_range_women_license_holders[bucket].add( license_holder )
					age_range_women_attendee_count[bucket] += 1
			
			event_data = {
				'name':event.name,
				'attendees':attendee_data,
				'attendees_men': sum(1 for p in attendee_data if p[0] == 0),
				'attendees_women': sum(1 for p in attendee_data if p[0] == 1),
				'participants_men': sum(1 for p in participant_data if p[0] == 0),
				'participants_women': sum(1 for p in participant_data if p[0] == 1),
			}
			event_data['attendees_total'] = event_data['attendees_men'] + event_data['attendees_women']
			event_data['participant_total'] = event_data['participants_men'] + event_data['participants_women']
			
			competition_data['attendees_men'] += event_data['attendees_men']
			competition_data['attendees_women'] += event_data['attendees_women']
			
			competition_data['participants_men'] += event_data['participants_men']
			competition_data['participants_women'] += event_data['participants_women']
			
			competition_data['events'].append( event_data )
		
		competition_data['attendees_total'] = competition_data['attendees_men'] + competition_data['attendees_women']
		data.append( competition_data )
	
	age_range_average = [
		0 if not age_range_license_holders[i] else age_range_attendee_count[i] / float(len(age_range_license_holders[i]))
		for i in xrange(len(age_range_attendee_count))
	]
	age_range_men_average = [
		0 if not age_range_men_license_holders[i] else age_range_men_attendee_count[i] / float(len(age_range_men_license_holders[i]))
		for i in xrange(len(age_range_men_attendee_count))
	]
	age_range_women_average = [
		0 if not age_range_women_license_holders[i] else age_range_women_attendee_count[i] / float(len(age_range_women_license_holders[i]))
		for i in xrange(len(age_range_women_attendee_count))
	]
	
	def trim_right_zeros( a ):
		for i in xrange(len(a)-1, -1, -1):
			if a[i]:
				del a[i+1:]
				break
	
	trim_right_zeros( age_range_average )
	trim_right_zeros( age_range_men_average )
	trim_right_zeros( age_range_women_average )
	
	license_holder_profile = []
	license_holder_men_profile = []
	license_holder_women_profile = []
	if profile_year:
		license_holder_profile = sorted(fix_age(profile_year - lh.date_of_birth.year) for lh in license_holders_set)
		license_holder_men_profile = sorted(fix_age(profile_year - lh.date_of_birth.year) for lh in license_holders_set if lh.gender == 0)
		license_holder_women_profile = sorted(fix_age(profile_year - lh.date_of_birth.year) for lh in license_holders_set if lh.gender == 1)
	else:
		profile_year = datetime.date.today().year
		
	attendees_total = sum(c['attendees_total'] for c in data)
	
	def format_int_percent( num, total ):
		return {'v':num, 'f':'{} / {} ({:.2f}%)'.format(num, total, (100.0 * num) / (total or 1))}
	
	def format_int_percent_event( num, total, event ):
		return {'v':num, 'f':'{} / {} ({:.2f}%) - {}'.format(num, total, (100.0 * num) / (total or 1), event)}
	
	def format_event_int_percent( num, total, event ):
		return {'v':num, 'f':'{}: {} / {} ({:.2f}%)'.format(event, num, total, (100.0 * num) / (total or 1))}
	
	# Initialize the category total.
	category_total = [['Category', 'Total']] + sorted( ([k, v] for k, v in category_total_overall.iteritems()), key=lambda x: x[1], reverse=True )
	
	#--------------
	ccc = [['Competition'] + [name for name, count in category_total[1:]]]
	for competition in sorted( (category_competition_total.iterkeys()), key=lambda x: x.start_date ):
		ccc.append( [competition.name] +
			[format_int_percent_event(
					category_competition_total[competition].get(name, 0),
					competition_participant_total[competition],
					competition_category_event.get(competition,{}).get(name,''),
				) if category_competition_total[competition].get(name, 0) != 0 else 0 for name, count in category_total[1:]] )
	
	# Add cumulative percent to the category total.
	category_total[0].append( 'Cumulative %' )
	cumulativePercent = 0.0
	for c in category_total[1:]:
		cumulativePercent += 100.0*c[-1] / participant_total
		c.append( cumulativePercent )
	
	event_max = max(len(events) for events in event_competition_participant_total.itervalues()) if event_competition_participant_total else 0
	eee = [['Competition'] + ['{}'.format(i+1) for i in xrange(event_max)]]
	for competition in sorted( (event_competition_participant_total.iterkeys()), key=lambda x: x.start_date ):
		events = sorted( ((event, count) for event, count in event_competition_participant_total[competition].iteritems()), key=lambda x: x[0].date_time )
		eee.append( [competition.name] +
			[format_event_int_percent(
					events[i][1],
					competition_participant_total[competition],
					events[i][0].name,
				) if i < len(events) else 0 for i in xrange(event_max)] )
	
	def get_expected_age( ac ):
		if not ac:
			return None
		most_frequent = max( v for v in ac.itervalues() )
		for a, c in ac.iteritems():
			if c == most_frequent:
				return a
		return None
	
	payload = {
		'competitions_total': competitions_total,
		'events_total': events_total,
		
		'attendees_total': attendees_total,
		'attendees_men_total': sum(c['attendees_men'] for c in data),
		'attendees_women_total': sum(c['attendees_women'] for c in data),
		
		'participant_total' : participant_total,
		
		'license_holders_attendance_total': len(license_holders_attendance_total),
		'license_holders_men_total': len(license_holders_men_total),
		'license_holders_women_total': len(license_holders_women_total),
		
		'attendance_average': sum(v for v in license_holders_attendance_total.itervalues()) / (float(len(license_holders_attendance_total)) or 1),
		'attendance_men_average': sum(v for v in license_holders_men_total.itervalues()) / (float(len(license_holders_men_total)) or 1),
		'attendance_women_average': sum(v for v in license_holders_women_total.itervalues()) / (float(len(license_holders_women_total)) or 1),
		
		'age_range_average':age_range_average,
		'age_range_men_average':age_range_men_average,
		'age_range_women_average':age_range_women_average,
		'age_increment': age_increment,
		
		'profile_year':profile_year,
		'license_holder_profile':license_holder_profile,
		'license_holder_men_profile':license_holder_men_profile,
		'license_holder_women_profile':license_holder_women_profile,
		
		'category_total':category_total,
		'category_competition_count':ccc,
		'event_competition_count':eee,
		
		'competitions': data,
	}
	return payload, sorted( license_holders_event_errors, key=lambda x: (x[1].date_time, x[0].date_of_birth) )
