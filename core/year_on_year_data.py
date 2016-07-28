
import datetime
import utils
import operator
from collections import defaultdict
from StringIO import StringIO
from models import *

def year_on_year_data( discipline=None, race_class=None, organizers=None, include_labels=None, exclude_labels=None ):
	discipline = int(discipline or -1)
	race_class = int(race_class or -1)

	competitions = Competition.objects.all()
	if discipline > 0:
		competitions = competitions.filter( discipline__pk = discipline )
	if race_class > 0:
		competitions = competitions.filter( race_class__pk = race_class )
	if organizers:
		competitions = competitions.filter( organizer__in = organizers )
	if include_labels:
		competitions = competitions.filter( report_labels__in = include_labels )
	if exclude_labels:
		competitions = competitions.exclude( report_labels__in = exclude_labels )
	
	all_events = []
	for c in competitions:
		all_events.extend( c.get_events() )
	all_events.sort( key=(lambda e: e.date_time) )
	
	year_on_year = []
	license_holders_year = []
	license_holders_all = set()
	events_by_day = defaultdict( list )
	
	competition_set = set()
	
	for event in all_events:
		if not event.has_participants():
			continue
		
		event_date = event.date_time.date()
		event_year = event_date.year
		if not year_on_year or year_on_year[-1]['year'] != event_year:
			year_on_year.append( {'year':event_year} )
			license_holders_year.append( set() )
			
			year_cur = year_on_year[-1]
			
			def add_to_value( k, v ):
				year_cur[k] = year_cur.get(k, 0) + v
			
			license_holders = set()
			license_holders_men = set()
			license_holders_women = set()
	
		if event.competition not in competition_set:
			add_to_value( 'competitions_total', 1 )
			competition_set.add( event.competition )
			
		events_by_day[event_date].append( event )
		
		add_to_value( 'events_total', 1 )
		
		for participant in event.get_participants():
			license_holders.add( participant.license_holder )
			add_to_value( 'participants_total', 1 )
			if participant.license_holder.gender == 0:
				license_holders_men.add( participant.license_holder )
				add_to_value( 'participants_men_total', 1 )
			else:
				license_holders_women.add( participant.license_holder )
				add_to_value( 'participants_women_total', 1 )
	
		add_to_value( 'attendees_total', len(license_holders) )
		add_to_value( 'attendees_men_total', len(license_holders_men) )
		add_to_value( 'attendees_women_total', len(license_holders_women) )
		license_holders_year[-1] |= license_holders
		license_holders_all |= license_holders

	if not year_on_year:
		return {}
		
	years = [yoy['year'] for yoy in year_on_year]
	attendees_total_year = [yoy['attendees_total'] for yoy in year_on_year]
	license_holders_total_year = [len(lh) for lh in license_holders_year]
	attendees_total = sum( yoy['attendees_total'] for yoy in year_on_year )
	attendees_men_total = sum( yoy['attendees_men_total'] for yoy in year_on_year )
	attendees_women_total = sum( yoy['attendees_women_total'] for yoy in year_on_year )
	def add_year_label( a ):
		return [['Year', 'Total']] + [[unicode(y),{'v':v, 'f':'{}: {:.2f}%'.format(v, 0.0 if not att else (v*100.0/att))}]
				for y, v, att in zip(years, a, license_holders_total_year)]
		
	last_year_but_not_this_year = [0]
	some_year_but_not_this_year = [0]
	license_holders_previous = set(list(license_holders_year[0]))
	for i in xrange(1,len(license_holders_year)):
		last_year_but_not_this_year.append( 0 )
		some_year_but_not_this_year.append( 0 )
		for lh in license_holders_year[i-1]:
			if lh not in license_holders_year[i]:
				last_year_but_not_this_year[-1] += 1
		for lh in license_holders_previous:
			if lh not in license_holders_year[i]:
				some_year_but_not_this_year[-1] += 1
		license_holders_previous |= license_holders_year[i]
	
	license_holders_profile = [defaultdict(int) for i in xrange(len(license_holders_year))]
	for i in xrange(len(license_holders_year)):
		for lh in license_holders_year[i]:
			for j in xrange(i, -1, -1):
				if lh not in license_holders_year[j]:
					break
			prev_years = i - j - 1 if i != 0 else 0
			license_holders_profile[i][prev_years] += 1
	
	participants_total = [['{}'.format(y), yoy['participants_total']] for y, yoy in zip(years, year_on_year)]
	participants_total.insert( 0, ['Year', 'Total'] )
	
	if license_holders_profile:
		max_profile = max( max(ap.iterkeys()) for ap in license_holders_profile ) + 1
		license_holders_profile_list = [[0] * max_profile for ap in license_holders_profile]
		for apl, app in zip(license_holders_profile_list, license_holders_profile):
			for k, v in app.iteritems():
				apl[k] = v
		license_holders_profile = license_holders_profile_list
		license_holders_profile = [['{}'.format(y)] + [{'v':v, 'f':'{}: {:.2f}%'.format(v, 0.0 if not att else (v*100.0/att))} for v in ap]
			for y, ap, att in zip(years, license_holders_profile, license_holders_total_year)]
		license_holders_profile.insert( 0, ['Year'] + ['{}'.format(i) for i in xrange(max_profile)] )
	
	def format_competitions_events( d, events ):
		events.sort( key=lambda e: (e.competition.name, e.date_time) )
		counts = [event.get_participant_count() for event in events]
		participants_total = sum( counts )
		
		competition_counts = defaultdict( int )
		for event, count in zip(events, counts):
			competition_counts[event.competition] += count
		
		out = StringIO()
		out.write( u'<div style="padding:5px 5px 5px 5px">' )
		out.write( u'<strong>{}:</strong>&nbsp;{}<br/>'.format(participants_total, d.strftime('%Y-%m-%d')) )
		
		competition_last = None
		for event, count in zip(events, counts):
			if event.competition != competition_last:
				if competition_last is not None:
					out.write( u'</ul>' )
				out.write( u'<strong>{}:&nbsp;</strong>&nbsp;{}<ul>'.format(competition_counts[event.competition], event.competition.name.replace(u' ', u'&nbsp;') ) )
				competition_last = event.competition
			out.write( u'<li><strong>{}:</strong>&nbsp;{}</li>'.format(count, event.name.replace(u' ', u'&nbsp;')) )
		
		out.write( u'</ul></div>' )
		return [[d.year, d.month-1, d.day], participants_total, out.getvalue()]
		
	calendar = sorted( format_competitions_events(d, v) for d, v in events_by_day.iteritems() )
	if calendar:
		year_min = min( c[0][0] for c in calendar )
		year_max = max( c[0][0] for c in calendar )
	else:
		year_min = year_max = 1970
	
	payload = {
		'competitions_total': sum( yoy['competitions_total'] for yoy in year_on_year ),
		'events_total': sum( yoy['events_total'] for yoy in year_on_year ),
		
		'attendees_total': attendees_total,
		'attendees_men_total': attendees_men_total,
		'attendees_women_total': attendees_women_total,
		
		'license_holders_attendance_total': len(license_holders_all),
		
		'license_holders_profile': license_holders_profile,
		'last_year_but_not_this_year': add_year_label(last_year_but_not_this_year),
		'some_year_but_not_this_year': add_year_label(some_year_but_not_this_year),
		'participants_total': participants_total,
		'calendar': calendar,
		'calendar_height': (year_max - year_min + 1) * 150,
	}
	return payload
