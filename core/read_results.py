import pytz
import re
import datetime

from models import *
import DurationField

from django.utils import timezone

reNonDigit = re.compile( r'[^\d]' )
def get_event_from_payload( payload ):
	# Create an timestamp in server time.
	raceScheduledLocalList = [int(f) for f in reNonDigit.sub( ' ', payload['raceScheduledStart'] ).split()]
	raceScheduledLocal = datetime.datetime(*raceScheduledLocalList)
	
	default_tz = timezone.get_default_timezone()
	raceScheduledStart = default_tz.localize( raceScheduledLocal )
	raceNameText = payload['raceNameText']
	
	EventClass = EventTT if payload.get('isTimeTrial', False) else EventMassStart
	
	for event in EventClass.objects.filter(date_time=raceScheduledStart).select_related('competition'):
		raceNameTextCur = u'-'.join( [event.competition.name, event.name] )
		if raceNameText == raceNameTextCur:
			return event
	
	return None
	
def read_results_crossmgr( payload ):
	warnings = []
	errors = []

	event = get_event_from_payload( payload )
	if not event:
		errors.append( 'Cannot find Event "{}", "{}"'.format(payload['raceNameText'], payload['raceScheduledStart']) )
		return errors, warnings
		
	competition = event.competition
	
	# Remove existing results.
	Result = event.get_result_class()
	Result.objects.filter( event=event ).delete()
	
	name_to_status_code = { name:code for code,name in Result.STATUS_CODE_NAMES }
	name_gender_to_category = { (c.code, c.gender):c for c in event.get_categories() }
	
	# Data is indexed by integer bib number.
	data = {int(k):v for k, v in payload['data'].iteritems()}
	
	# Get the category for each bib.
	def get_name_gender( cat_str ):
		for gender_code, g in enumerate(('(Men)', '(Women)', '(Open)')):
			if cat_str.endswith(g):
				return cat_str[:-len(g)].strip(), gender_code
		return cat_str, None
				
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
	for cd in payload['catDetails']:
		if cd['catType'] != 'Start Wave' or cd['name'] == 'All':
			continue
		
		wave_starters = cd['starters']
		for wave_rank, bib in enumerate(cd['pos'], 1):
			try:
				d = data[bib]
			except KeyError:
				continue
			
			try:
				category = bib_category[bib]
			except KeyError:
				warnings.append( 'Cannot find category for bib={}'.format(bib) )
				continue
				
			try:
				participant = competition.participant_set.get(bib=bib, category=category)
			except Exception as e:
				warnings.append( 'Problem finding participant bib={}, category="{}": {}'.format(bib, category.full_name, e) )
				continue
			
			race_times = d.get('raceTimes',[] )
			if len(race_times) < 2:
				race_times = []
			
			fields = dict(
				event=event,
				participant=participant,
				status=name_to_status_code.get(d['status'], 'Finisher'),
				finish_time=DurationField.formatted_timedelta(seconds=race_times[-1]) if race_times else None,
				
				category_rank=bib_category_rank[bib],
				category_starters=category_starters[category],
				category_gap = bib_category_gap[bib],
				
				wave_rank=wave_rank,
				wave_starters=wave_starters,
				wave_gap = format_gap( cd, wave_rank )
			)
			add_if_exists( fields, 'adjustment_time', d, 'ttPenalty' )
			add_if_exists( fields, 'adjustment_note', d, 'ttNote' )

			result = Result( **fields )
			result.save()			
			result.set_race_times( race_times )
		
	return {'errors': errors, 'warnings': warnings}