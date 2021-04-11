import re
import pytz
import datetime
from collections import defaultdict

from .models import *
from .DurationField import formatted_timedelta

reNonDigit = re.compile( r'[^\d]' )
def get_event_from_payload( payload ):
	raceScheduledLocalList = [int(f) for f in reNonDigit.sub( ' ', payload['raceScheduledStart'] ).split()]
	raceScheduledLocal = datetime.datetime(*raceScheduledLocalList)
	
	info = []
	def info_append( info_text ):
		info.append( info_text )
		safe_print( info_text )
	
	try:
		tz = pytz.timezone(payload['raceTimeZone'])
	except Exception as e:
		# Default to the server timezone.
		tz = timezone.get_default_timezone()
	
	raceScheduledStart = tz.localize( raceScheduledLocal )
	raceNameText = payload['raceNameText']
	
	EventClass = EventTT if payload.get('isTimeTrial', False) else EventMassStart
	
	if not EventClass.objects.filter(date_time=raceScheduledStart).exists():
		info_append( u"Cannot find an Event starting at {}".format( raceScheduledStart.strftime('%Y-%m-%d %H:%M %z') ) )
	
	for event in EventClass.objects.filter(date_time=raceScheduledStart).select_related('competition'):
		raceNameTextCur = u'-'.join( [event.competition.name, event.name] )
		info_append( u'Checking by Event: "{}" = "{}"'.format(raceNameText, raceNameTextCur) )
		if raceNameText == raceNameTextCur:
			info_append( u'Success.' )
			return event, info
	
	for event in EventClass.objects.filter(date_time=raceScheduledStart).select_related('competition'):
		for wave in event.get_wave_set().all():
			raceNameTextCur = u'-'.join( [event.competition.name, wave.name] )
			info_append( u'Checking by Wave: "{}" = "{}"'.format(raceNameText, raceNameTextCur) )
			if raceNameText == raceNameTextCur:
				info_append( u'Success.' )
				return event, info
	
	info_append( u'Failure.' )
	return None, info
	
def read_results_crossmgr( payload ):
	warnings = []
	errors = []

	event, info = get_event_from_payload( payload )
	if not event:
		errors.append( u'Cannot find Event "{}", "{}"'.format(payload['raceNameText'], payload['raceScheduledStart']) )
		return { 'errors': errors, 'warnings': warnings, 'info':info }
		
	competition = event.competition
	
	# Remove existing results.
	Result = event.get_result_class()
	Result.objects.filter( event=event ).delete()
	
	name_to_status_code = { name:code for code,name in Result.STATUS_CODE_NAMES }
	name_gender_to_category = { (c.code, c.gender):c for c in event.get_categories() }
	
	# Data is indexed by integer bib number.
	data = {int(k):v for k, v in payload['data'].items()}
	
	# Get the category for each bib.
	reGender = re.compile( r'(\([^)]+\))$' )
	def get_name_gender( cat_str ):
		try:
			gender_in_brackets = reGender.search( cat_str ).group(1)
		except:
			return cat_str, None
		
		cat_name = cat_str[:-len(gender_in_brackets)].strip()
		gender_name = gender_in_brackets[1:-1].strip().upper()
		
		gender_code = None
		if   gender_name in (u'MEN', u'HOMMES', u'HOMBRES', u'UOMINI', u'HOMENS'):
			gender_code = 0
		elif gender_name in (u'WOMEN', u'FEMMES', u'MUJER'):
			gender_code = 1
		elif gender_name in (u'OPEN', u'OUVRIR', u'ABIERTO'):
			gender_code = 2
		
		if gender_code is None:
			gender_char = gender_name.strip()[0]
			if   gender_char in 'MHU':
				gender_code = 0
			elif gender_char in 'WF':
				gender_code = 1
			else:
				gender_code = 2
		
		return cat_name, gender_code
				
	def format_gap( cd, rank ):
		try:
			g = cd['gapValue'][rank-1]
		except:
			return ''
		if g > 0:
			return utils.format_time_gap( g )
		elif g < 0:
			return '{} {}'.format(g, 'lap'  if g == -1 else 'laps')
		return u''
		
	bib_category = {}
	bib_category_rank = {}
	bib_category_gap = {}
	category_starters = {}
	
	for cd in payload['catDetails']:
		if cd['catType'] == 'Custom':
			continue
		category = name_gender_to_category.get( get_name_gender(cd['name']), None )
		if not category:
			continue
		
		category_starters[category] = cd['starters']
		for category_rank, bib in enumerate(cd['pos'], 1):
			bib_category[bib] = category
			bib_category_rank[bib] = category_rank
			bib_category_gap[bib] = format_gap( cd, category_rank )
	
	def add_if_exists( fields, f, rr, a ):
		try:
			fields[f] = rr[a]
		except KeyError:
			pass
	
	# Record results by start wave.
	# To get results by wave, select all category in the wave and order by rank.
	# To get results by category, select by that category and order by rank.
	rtcs_cache = defaultdict( list )
	def flush_cache():
		for cls, objs in rtcs_cache.items():
			cls.objects.bulk_create( objs )
			del objs[:]
	
	prime_points = {p['winnerBib']:p['points'] for p in payload.get('primes',[]) if p.get('points',None) }
	prime_time_bonus = {p['winnerBib']:formatted_timedelta(seconds=p['timeBonus']) for p in payload.get('primes',[]) if p.get('timeBonus',None) }
	
	for cd in payload['catDetails']:
		if cd['catType'] != 'Start Wave' or cd['name'] == 'All':
			continue
		
		distance_unit = cd.get('distanceUnit', 'km')
		unit_conversion = 1.0 if distance_unit == 'km' else 1.609344
		wave_starters = cd['starters']
		for wave_rank, bib in enumerate(cd['pos'], 1):
			try:
				d = data[bib]
			except KeyError:
				continue
			
			try:
				category = bib_category[bib]
			except KeyError:
				warnings.append( u'Cannot find category for bib={}'.format(bib) )
				continue
				
			participant = None
			if not participant and d.get('License', ''):
				participant = competition.participant_set.filter( license_holder__license_code=d['License'], category=category ).first()
			if not participant:
				participant = competition.participant_set.filter( bib=bib, category=category ).first()
			if not participant and d.get('LastName', ''):
				participant = competition.participant_set.filter(
					license_holder__search_text__startswith=utils.get_search_text( [n for n in (d.get('LastName',''), d.get('FirstName','')) if n] ),
					category=category
				).first()
			
			if not participant:
				warnings.append( u'Cannot find Participant bib={} name="{}, {}", category="{}"'.format(
					bib, d.get('LastName',''), d.get('FirstName',''), category.full_name()) )
				continue
			
			race_times = d.get('raceTimes',[] )
			if len(race_times) < 2:
				race_times = []
			
			lap_speeds = [ls*unit_conversion for ls in d.get('lapSpeeds',[])]
			
			ave_kmh = None
			speed = d.get('speed',0.0)
			if speed:
				try:
					s, u = speed.split()
					ave_kmh = float(s) * unit_conversion
				except:
					pass
			
			fields = dict(
				event=event,
				participant=participant,
				status=name_to_status_code.get(d['status'], 'Finisher'),
				finish_time=formatted_timedelta(seconds=race_times[-1]) if race_times else None,
				
				category_rank=bib_category_rank[bib],
				category_starters=category_starters[category],
				category_gap = bib_category_gap[bib],
				
				wave_rank=wave_rank,
				wave_starters=wave_starters,
				wave_gap = format_gap( cd, wave_rank ),				
			)
			add_if_exists( fields, 'adjustment_time', d, 'ttPenalty' )
			add_if_exists( fields, 'adjustment_note', d, 'ttNote' )
			add_if_exists( fields, 'relegated', d, 'relegated' )
			fields['relegated'] = bool(fields.get('relegated',None))	# Force value to True or False.
			if bib in prime_points:
				fields['points'] = prime_points[bib]
			if bib in prime_time_bonus:
				fields['time_bonus'] = prime_time_bonus[bib]
			if ave_kmh:
				fields['ave_kmh'] = ave_kmh

			result = Result( **fields )
			try:
				result.save()
				rtcs = result.set_race_times( race_times, lap_speeds, do_create=False )
				if rtcs:
					rtcs_cache[type(rtcs[0])].extend( rtcs )
					if any( len(objs) >= 999 for objs in rtcs_cache.values() ):
						flush_cache()
			except Exception as e:
				warnings.append( u'Cannot Create Result bib={} name="{}, {}", category="{}" ({})'.format(
					bib, d.get('LastName',''), d.get('FirstName',''), category.full_name(), e) )
				continue

	flush_cache()		
	return {'errors': errors, 'warnings': warnings, 'name':u'{}-{}'.format(competition.name, event.name)}
