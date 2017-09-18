
import datetime
import utils
from collections import defaultdict
from models import *

def get_competitions( start_date=None, end_date=None, disciplines=None, race_classes=None, organizers=None, include_labels=None, exclude_labels=None ):
	competitions = Competition.objects.all()
	if start_date is not None:
		competitions = competitions.filter( start_date__gte = start_date )
	if end_date is not None:
		competitions = competitions.filter( start_date__lte = end_date )
	if disciplines:
		competitions = competitions.filter( discipline__pk__in = disciplines )
	if race_classes:
		competitions = competitions.filter( race_class__pk__in = race_classes )
	if organizers:
		competitions = competitions.filter( organizer__in = organizers )
	if include_labels:
		competitions = competitions.filter( report_labels__in = include_labels )
	if exclude_labels:
		competitions = competitions.exclude( report_labels__in = exclude_labels )
	return competitions.order_by( 'start_date', 'pk' ).distinct()
	
def participation_data( start_date=None, end_date=None, disciplines=None, race_classes=None, organizers=None, include_labels=None, exclude_labels=None ):
	competitions = get_competitions( start_date, end_date, disciplines, race_classes, organizers, include_labels, exclude_labels )
	license_holders_event_errors = set()
	
	data = []
	license_holders_attendance_total = defaultdict( int )
	license_holders_men_total = defaultdict( int )
	license_holders_women_total = defaultdict( int )
	
	category_total_overall = defaultdict( int )
	category_competition_total = defaultdict( lambda: defaultdict(int) )
	event_competition_participants_total = defaultdict( lambda: defaultdict(int) )
	competition_attendee_total = defaultdict( int )
	competition_participants_total = defaultdict( int )
	category_max_overall = defaultdict( int )
	
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
	participants_total = 0
	prereg_participants_total = 0
	competitions_total, events_total = 0, 0
	
	discipline_overall = defaultdict( set )
	discipline_men = defaultdict( set )
	discipline_women = defaultdict( set )
	discipline_bucket = defaultdict( lambda: defaultdict(set) )
	
	def fix_age( age ):
		return max(min(age, 119), 0)
	
	for competition in competitions:
		if not competition.has_participants():
			continue
		
		discipline_name = competition.discipline.name

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
			'participants_total': 0,
			
			'participants_men_dnf': 0,
			'participants_women_dnf': 0,
			'participants_total_dnf': 0,
			
			'participants_men_dns': 0,
			'participants_women_dns': 0,
			'participants_total_dns': 0,
			
			'prereg_participants_men': 0,
			'prereg_participants_women': 0,
			
			'participants_paid_seasons_pass': 0,
			'participants_paid_on_venue': 0,
			'participants_unpaid': 0,
		}
		for event in competition.get_events():
			if not event.has_participants():
				continue
				
			events_total += 1
			
			attendee_data = []
			participant_data = []
			prereg_participant_data = []
			event_license_holders = set()
			for participant in event.get_participants():
				
				# Participation.
				license_holder = participant.license_holder
				age = event.date_time.year - license_holder.date_of_birth.year
				if not (7 < age < 100):
					license_holders_event_errors.add( (license_holder, event) )
				age = fix_age( age )
				
				event_competition_participants_total[competition][event] += 1
				category_name = participant.category.code_gender if participant.category else unicode(_('Unknown'))
				category_total_overall[category_name] += 1
				category_competition_total[competition][category_name] += 1
				competition_category_event[competition][category_name] = event.name
				competition_participants_total[competition] += 1
				participants_total += 1
				participant_data.append( [license_holder.gender, age] )
				if participant.preregistered:
					prereg_participants_total += 1
					prereg_participant_data.append( [license_holder.gender, age] )
				
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
				
				discipline_overall[discipline_name].add( license_holder )
				discipline_bucket[discipline_name][bucket].add( license_holder )
				
				if license_holder.gender == 0:
					license_holders_men_total[license_holder] += 1
					age_range_men_license_holders[bucket].add( license_holder )
					age_range_men_attendee_count[bucket] += 1
					discipline_men[discipline_name].add( license_holder )
				else:
					license_holders_women_total[license_holder] += 1
					age_range_women_license_holders[bucket].add( license_holder )
					age_range_women_attendee_count[bucket] += 1
					discipline_women[discipline_name].add( license_holder )
					
			event_men_dnf   = event.get_results().filter( status=Result.cDNF, participant__license_holder__gender=0 ).count()
			event_men_dns   = event.get_results().filter( status=Result.cDNS, participant__license_holder__gender=0 ).count()
			event_women_dnf = event.get_results().filter( status=Result.cDNF, participant__license_holder__gender=1 ).count()
			event_women_dns = event.get_results().filter( status=Result.cDNS, participant__license_holder__gender=1 ).count()
				
			event_data = {
				'name':event.name,
				'attendees':attendee_data,
				'attendees_men': sum(1 for p in attendee_data if p[0] == 0),
				'attendees_women': sum(1 for p in attendee_data if p[0] == 1),
				'participants_men': sum(1 for p in participant_data if p[0] == 0),
				'participants_women': sum(1 for p in participant_data if p[0] == 1),
				'prereg_participants_men': sum(1 for p in prereg_participant_data if p[0] == 0),
				'prereg_participants_women': sum(1 for p in prereg_participant_data if p[0] == 1),
				
				'men_dnf': event_men_dnf,
				'men_dns': event_men_dns,
				'women_dnf': event_women_dnf,
				'women_dns': event_women_dns,
				'total_dnf': event_men_dnf + event_women_dnf,
				'total_dns': event_men_dns + event_women_dns,
			}
			event_data['attendees_total'] = event_data['attendees_men'] + event_data['attendees_women']
			event_data['participants_total'] = event_data['participants_men'] + event_data['participants_women']
			event_data['prereg_participants_total'] = event_data['prereg_participants_men'] + event_data['prereg_participants_women']			
			
			competition_data['attendees_men'] += event_data['attendees_men']
			competition_data['attendees_women'] += event_data['attendees_women']
			
			competition_data['participants_men'] += event_data['participants_men']
			competition_data['participants_women'] += event_data['participants_women']
			
			competition_data['participants_men_dnf'] += event_data['men_dnf']
			competition_data['participants_men_dns'] += event_data['men_dns']
			competition_data['participants_women_dnf'] += event_data['women_dnf']
			competition_data['participants_women_dns'] += event_data['women_dns']
			
			competition_data['prereg_participants_men'] += event_data['prereg_participants_men']
			competition_data['prereg_participants_women'] += event_data['prereg_participants_women']
			
			competition_data['events'].append( event_data )
		
		competition_data['attendees_total'] = competition_data['attendees_men'] + competition_data['attendees_women']
		competition_data['participants_total'] = competition_data['participants_men'] + competition_data['participants_women']
		competition_data['prereg_participants_total'] = competition_data['prereg_participants_men'] + competition_data['prereg_participants_women']
		competition_data['participants_total_dnf'] = competition_data['participants_men_dnf'] + competition_data['participants_women_dnf']
		competition_data['participants_total_dns'] = competition_data['participants_men_dns'] + competition_data['participants_women_dns']

		#------------------------------------------------
		if competition.seasons_pass:
			competition_data['participants_paid_seasons_pass'] = Participant.objects.filter(
				competition=competition,
				role=Participant.Competitor,
				paid=True,
				license_holder__in=SeasonsPassHolder.objects.filter(seasons_pass=competition.seasons_pass).values_list('license_holder', flat=True)
			).count()
			competition_data['participants_paid_on_venue'] = Participant.objects.filter(
				competition=competition,
				role=Participant.Competitor,
				paid=True
			).exclude(
				license_holder__in=SeasonsPassHolder.objects.filter(seasons_pass=competition.seasons_pass).values_list('license_holder', flat=True)
			).count()
		else:
			competition_data['participants_paid_on_venue'] = Participant.objects.filter(
				competition=competition,
				role=Participant.Competitor,
				paid=True
			).count()
		competition_data['participants_unpaid'] = Participant.objects.filter(competition=competition, paid=False).count()
		
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
		profile_year = timezone.now().date().year
		
	attendees_total = sum(c['attendees_total'] for c in data)
	
	def format_int_percent( num, total ):
		return {'v':num, 'f':'{} / {} ({:.2f}%)'.format(num, total, (100.0 * num) / (total or 1))}
	
	def format_int_percent_event( num, total, event ):
		return {'v':num, 'f':'{} / {} ({:.2f}%) - {}'.format(num, total, (100.0 * num) / (total or 1), event)}
	
	def format_event_int_percent( num, total, event ):
		return {'v':num, 'f':'{}: {} / {} ({:.2f}%)'.format(event, num, total, (100.0 * num) / (total or 1))}
		
	def format_percent( num, total ):
		percent = 100.0 * float(num) / float(total if total else 1.0)
		return {'v':percent, 'f':'{:.2f}%'.format(percent)}
	
	# Initialize the category total.
	category_total = [['Category', 'Total']] + sorted( ([k, v] for k, v in category_total_overall.iteritems()), key=lambda x: x[1], reverse=True )
	category_total_men = [['Category', 'Total']] + [[re.sub(r' \(Men\)$', '', c), t] for c, t in category_total[1:] if c.endswith( ' (Men)' )]
	category_total_women = [['Category', 'Total']] + [[re.sub(r' \(Women\)$', '', c), t] for c, t in category_total[1:] if c.endswith( ' (Women)' )]
	category_total_open = [['Category', 'Total']] + [[re.sub(r' \(Open\)$', '', c), t] for c, t in category_total[1:] if c.endswith( ' (Open)' )]
	
	#--------------
	ccc = [['Competition'] + [name for name, count in category_total[1:]]]
	for competition in sorted( (category_competition_total.iterkeys()), key=lambda x: x.start_date ):
		ccc.append( [competition.name] +
			[format_int_percent_event(
					category_competition_total[competition].get(name, 0),
					competition_participants_total[competition],
					competition_category_event.get(competition,{}).get(name,''),
				) if category_competition_total[competition].get(name, 0) != 0 else 0 for name, count in category_total[1:]] )
	
	# Add cumulative percent to the category total.
	for ct in [category_total, category_total_men, category_total_women, category_total_open]:
		ct[0].append( 'Cumulative %' )
		ct_total = sum( t for c, t in ct[1:] )
		cumulativePercent = 0.0
		for c in ct[1:]:
			cumulativePercent += 100.0*c[-1] / ct_total
			c.append( cumulativePercent )
	
	event_max = max(len(events) for events in event_competition_participants_total.itervalues()) if event_competition_participants_total else 0
	eee = [['Competition'] + ['{}'.format(i+1) for i in xrange(event_max)]]
	for competition in sorted( (event_competition_participants_total.iterkeys()), key=lambda x: x.start_date ):
		events = sorted( ((event, count) for event, count in event_competition_participants_total[competition].iteritems()), key=lambda x: x[0].date_time )
		eee.append( [competition.name] +
			[format_event_int_percent(
					events[i][1],
					competition_participants_total[competition],
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
		
	# Create a postal code hierarchy.
	postal_codes = defaultdict( int )
	for lh in license_holders_attendance_total.iterkeys():
		postal_codes['Unknown' if not lh.zip_postal else lh.zip_postal.replace(' ','')[:4]] += 1
	postal_code_data = [['/All/' + ('Unknown' if p == 'Unknown' else '/'.join( p[:i] for i in xrange(1, len(p)+1))), total] for p, total in postal_codes.iteritems()]
	
	#-----------------------------------------------
	# Discipline data.
	#
	def safe_union( *args ):
		return set.union( *args ) if args else set()

	discipline_total = len( safe_union( *[v for v in discipline_overall.itervalues()] ) )
	discipline_men_total = len( safe_union( *[v for v in discipline_men.itervalues()] ) )
	discipline_women_total = len( safe_union( *[v for v in discipline_women.itervalues()] ) )
	
	discipline_used = list(discipline_overall.iterkeys())
	discipline_used.sort( key=lambda d: len(discipline_overall[d]), reverse=True )
	
	discipline_overall = [[d, format_percent(len(discipline_overall[d]), discipline_total)] for d in discipline_used]
	discipline_overall.insert( 0, ['Discipline', 'All License Holders'] )
	discipline_gender = [
		[
			d,
			format_percent(len(discipline_men.get(d, set())), discipline_men_total),
			format_percent(len(discipline_women.get(d, set())), discipline_women_total)
		] for d in discipline_used]
	discipline_gender.insert( 0, ['Discipline', 'Men', 'Women'] )
	
	buckets_used = safe_union( *[set(b for b in discipline_bucket[d].iterkeys()) for d in discipline_used] )
	bucket_min = min( buckets_used ) if buckets_used else 0
	bucket_max = max( buckets_used ) + 1 if buckets_used else 0
	discipline_bucket_total = {b: len( safe_union(*[discipline_bucket[d].get(b,set())
		for d in discipline_used]))
			for b in xrange(bucket_min, bucket_max)
	}
	
	discipline_age = [[d] + [format_percent(len(discipline_bucket[d].get(b, set())), discipline_bucket_total.get(b, 0))
		for b in xrange(bucket_min, bucket_max)]
			for d in discipline_used]
	discipline_age.insert( 0, ['Discipline'] + ['{}-{}'.format(b*age_increment, (b+1)*age_increment-1)
		for b in xrange(bucket_min, bucket_max)]
	)
	
	#-----------------------------------------------
	# Average/Max Category
	#
	def getCategoryAverageMax():
		cct = defaultdict( lambda: defaultdict(int) )
		for competition, category_name_total in category_competition_total.iteritems():
			for category_name, total in category_name_total.iteritems():
				cct[category_name][competition] = total
		category_average_max = [
			[
				category_name,
				sum(competition_total.itervalues()) / float(len(competition_total)),
				max(competition_total.itervalues()),
			] for category_name, competition_total in cct.iteritems()
		]
		category_average_max.sort( key=lambda x: x[2], reverse=True )
		#category_average_max.insert( 0, ['Category', 'Ave', 'Max'] )
		return category_average_max
	category_average_max = getCategoryAverageMax()
	
	payload = {
		'competitions_total': competitions_total,
		'events_total': events_total,
		
		'attendees_total': attendees_total,
		'attendees_men_total': sum(c['attendees_men'] for c in data),
		'attendees_women_total': sum(c['attendees_women'] for c in data),
		
		'participants_total' : participants_total,
		'prereg_participants_total': prereg_participants_total,
		
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
		'category_total_men':category_total_men,
		'category_total_women':category_total_women,
		'category_total_open':category_total_open,
		'category_competition_count':ccc,
		'event_competition_count':eee,
		
		'postal_code_data':postal_code_data,
		'postal_codes':[[k,v] for k, v in postal_codes.iteritems() if k != 'Unknown'],
		
		'competitions': data,
		
		'discipline_total': discipline_total,
		'discipline_overall': discipline_overall,
		'discipline_gender': discipline_gender,
		'discipline_age': discipline_age,
		
		'discipline_used_len': len(discipline_used),
		
		'category_average_max': category_average_max,
	}
	return payload, sorted( license_holders_event_errors, key=lambda x: (x[1].date_time, x[0].date_of_birth) ), competitions.order_by('-start_date')
