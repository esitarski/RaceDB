from models import *

import os
import math
import datetime
import operator
import utils
from collections import defaultdict
from django.utils.safestring import mark_safe

def formatTime( secs, highPrecision = False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = secs % 60
	if highPrecision:
		secStr = '{:05.2f}'.format( secs + f )
	else:
		secStr = '{:02d}'.format( secs )
	
	if hours > 0:
		return "{}{}:{:02d}:{}".format(sign, hours, minutes, secStr)
	if minutes > 0:
		return "{}{}:{}".format(sign, minutes, secStr)
	return "{}{}".format(sign, secStr)
	
def formatTimeGap( secs, highPrecision = False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = secs % 60
	if highPrecision:
		decimal = '.%02d' % int( f * 100 )
	else:
		decimal = ''
	if hours > 0:
		return "%s%dh%d'%02d%s\"" % (sign, hours, minutes, secs, decimal)
	else:
		return "%s%d'%02d%s\"" % (sign, minutes, secs, decimal)

class EventResult( object ):

	slots__ = ('result', 'rank', 'starters', 'value_for_rank', 'category', 'ranking_criteria', 'upgrade_factor', 'upgraded', 'ignored')
	
	def __init__( self, result, rank, value_for_rank ):
		self.result = result
		self.rank = rank
		self.starters = starters
		
		self.value_for_rank = value_for_rank
		self.category = rank.participant.category
		self.ranking_criteria = ranking_criteria
		
		self.upgrade_factor = 1.0
		self.upgraded = False
		self.ignored = False
		
	@property:
	def status( self ):
		return self.result.status
		
	@property
	def event( self ):
		return self.result.event
		
	@property
	def participant( self ):
		return self.result.participant
		
	@property
	def team_name( self ):
		team = self.result.participant.team
		return team.name if team else u''
		
	@property
	def license_holder( self ):
		return self.result.participant.license_holder
		
	@property
	def status_rank( self ):
		if self.result.status == 0:
			return self.rank
		return 999999
	
	def get_rank_text( self ):
		if self.result.status != Result.cFinisher:
			return self.result.get_status_display()
		if self.ranking_criteria == 0:
			i = int(self.value_for_rank)
			if i == self.value_for_rank:
				return u'{}'.format(i)
			else:
				return u'{:.2f}'.format(self.value_for_rank)
		elif self.ranking_criteria == 1:
			return formatTime(self.value_for_rank)
		else:
			return u'{:.2f}'.format(self.value_for_rank)
	
	def get_format( self ):
		return (
			'{}'.format(self.get_rank_text()),
			'{}/{}'.format(self.rank, self.starters),
			self.upgraded,
			self.ignored,
		)

def extract_event_results( sce ):
	series = sce.series
	
	points_structure = sce.points_structure if series.ranking_criteria == 0 else None
	status_keep = [Result.cFinisher, Result.cPUL]
	if points_structure:
		get_points = points_structure.get_points_getter()
		if points_structure.dnf_points:
			status_keep.append( Result.cDNF )
		if points_structure.dnf_points:
			status_keep.append( Result.cDNS )
	else:
		get_points = None
	
	def get_rank( w, rr ):
		if w.rank_categories_together:
			return rr.wave_rank
		else:
			return rr.category_rank
			
	def get_starters( w, rr ):
		if w.rank_categories_together:
			return rr.wave_starters
		else:
			return rr.category_starters
			
	def get_value_for_rank( w, rr, rank, rrWinner ):
		if get_points:
			return get_points( rr, rr.status )
		if   series.ranking_criteria == 1:	# Time
			try:
				return rr.finish_time.total_seconds()
			except:
				return 24.0*60.0*60.0
		elif series.ranking_criteria == 2:	# % Winner / Time
			try:
				return 100.0 * rrWinner.finish_time.total_seconds() / rr.finish_time.total_seconds()
			except:
				return 0
		assert False, 'Unknown ranking criteria'
	
	eventResults = []
	for w in sce.event.get_wave_set().all():
		rr_winner = None
		for rr in w.get_results().filter(
				participant__category__in=series.get_category_pk() ).filter(
				status__in=status_keep ).select_related(
				'participant', 'participant__license_holder'
			).order_by('wave_rank'):
			if w.rank_categories_together:
				if not rr_winnner:
					rr_winner = rr
			else:
				if not rr_winner or rr_winner.participant.category != rr.participant.category:
					rr_winner = rr

			rank = get_rank( w, rr )
			value_for_rank = get_value_for_rank(w, rr, rank, rr_winner)
			if value_for_rank:
				eventResults.append( EventResult(rr, rank, value_for_rank, series.ranking_criteria) )

	return eventResults

def adjust_for_upgrades( series, eventResults ):
	upgradeCategoriesAll = set()
	factorPathPositions = []
	for sup in series.seriesupgradeprogression_set.all():
		if sup.factor == 0.0:
			continue
		path = list( suc.category for suc in sup.seriesupgradecategory_set.all() )
		position = {cat:i for i, cat in enumerate(path)}
		path = set( path )
		upgradeCategoriesAll |= path
		factorPathPositions.append( [sup.factor, path, position] )

	if not factorPathPositions:
		return
	
	# Organize results by license holder, then by category and result.
	competitionCategories = defaultdict( lambda: defaultdict(list) )
	for rr in eventResults:
		if rr.category in upgradeCategoriesAll:
			competitionCategories[rr.license_holder][rr.category].append( rr )
	
	for lh_categories in competitionCategories.itervalues():
		if len(lh_categories) == 1:
			continue
		
		for factor, path, position in factorPathPositions:
			upgradeCategories = { cat: rrs for cat, rrs in lh_categories.iteritems() if cat in path }
			if len(upgradeCategories) <= 1:
				continue
			
			highestposition, highestCategory = -1, None
			for cat in upgradeCategories.iterkeys():
				pos = position[cat]
				if pos > highestposition:
					highestposition, highestCategory = pos, cat
		
			for cat, rrs in upgradeCategories.iteritems():
				for rr in rrs:
					if rr.category != highestCategory:
						rr.category = highestCategory
						rr.factor = factor ** (highestposition - position[cat])
						rr.upgraded = True
		
			break

def series_results( series, categories, eventResults ):
	categories = set( list(categories) )
	scoreByTime = (series.ranking_criteria == 1)
	scoreByPercent = (series.ranking_criteria == 2)
	bestResultsToConsider = series.best_results_to_consider
	mustHaveCompleted = series.must_have_completed
	showLastToFirst = series.show_last_to_first
	considerMostEventsCompleted = series.consider_most_events_completed
	
	# Get all results for this category.
	eventResults = [rr for rr in eventResults if rr.category in categories]
	if not eventResults:
		return [], [], set()
	eventResults.sort( key=operator.attrgetter('event.date_time', 'rank') )
	
	# Assign a sequence number to the events.
	events = sorted( set(rr.result.event for rr in eventResults), key=operator.attrgetter('date_time') )
	eventSequence = {e:i for i, e in enumerate(events)}
	
	lhEventsCompleted = defaultdict( int )
	lhPlaceCount = defaultdict( lambda : defaultdict(int) )
	lhTeam = defaultdict( unicode )
	lhUpgrades = defaultdict( lambda : [False] * len(events) )
	lhNameLicense = {}
		
	lhResults = defaultdict( lambda : [None] * len(races) )
	lhFinishes = defaultdict( lambda : [None] * len(races) )
	
	lhValue = defaultdict( float )
	
	percentFormat = u'{:.2f}'
	floatFormat = u'{:0.2f}'
	
	# Get the individual results for each lh, and the total value.
	for rr in eventResults:
		lh = rr.license_holder
		lhTeam[lh] = rr.team
		lhResults[lh][eventSequence[rr.event]] = rr
		lhValue[lh] += rr.value_for_rank
		lhPlaceCount[lh][rr.rank] += 1
		lhEventsCompleted[lh] += 1
	
	# Adjust for the best times.
	if bestResultsToConsider > 0:
		for lh, rrs in lhResults.iteritems():
			iResults = [(i, rr) for i, rr in enumerate(rrs) if rr is not None]
			if len(iResults) > bestResultsToConsider:
				if scoreByTime:
					iResults.sort( key=lambda x: x[1].value_for_rank, x[0] )
				else:
					iResults.sort( key=lambda x: -x[1].value_for_rank, x[0] )
				for i, t in iResults[bestResultsToConsider:]:
					lhValue[lh] -= t
					rrs[i].ignored = True
				lhEventsCompleted[lh] = bestResultsToConsider

	# Filter out if minimal events are not completed.
	lhOrder = [lh for lh, results in lhResults.iteritems() if lhEventsCompleted[lh] >= mustHaveCompleted]
	
	# Sort by decreasing events completed, then increasing lh time.
	lhGap = {}
	if scoreByTime:
		# Sort by increasing time..
		lhOrder.sort( key = lambda r: (
				[-lhEventsCompleted[r], lhValue[r]] +
				[-lhPlaceCount[r][k] for k in xrange(1, numPlacesTieBreaker+1)] +
				[rr.status_rank if rr else 999999 for rr in lhResults[r]]
			)
		)
		# Compute the time gap.
		if lhOrder:
			leader = lhOrder[0]
			leaderValue = lhValue[leader]
			leaderEventsCompleted = lhEventsCompleted[leader]
			lhGap = { r : lhValue[r] - leaderValue if lhEventsCompleted[r] == leaderEventsCompleted else None for r in lhOrder }
			lhGap = { r : formatTime_gap(gap) if gap else u'' for r, gap in lhGap.iteritems() }
	
	else:
		# Sort by decreasing value.
		lhOrder.sort( key = lambda r: (
				[-lhValue[r]] +
				([-lhEventsCompleted[r]] if considerMostEventsCompleted else []) +
				[-lhPlaceCount[r][k] for k in xrange(1, numPlacesTieBreaker+1)] +
				[rr.status_rank if rr else 999999 for rr in lhResults[r]]
			)
		)
		
		# Compute the gap.
		lhGap = {}
		if lhOrder:
			leader = lhOrder[0]
			leaderValue = lhValue[leader]
			lhGap = { r : leaderValue - lhValue[r] for r in lhOrder }
			if scoreByPercent:
				lhGap = { r : percentFormat.format(gap) if gap else u'' for r, gap in lhGap.iteritems() }
			else:
				lhGap = { r : floatFormat.format(gap) if gap else u'' for r, gap in lhGap.iteritems() }
				
	# List of:
	# license_holder, team, totalValue, gap, [list of results for each event in series]
	categoryResult = [[lh, lhTeam[lh], lhValue[lh], lhGap[lh]] + [lhResults[lh]] for lh in lhOrder]
	if showLastToFirst:
		events.reverse()
		for lh, team, value, gap, results in categoryResult:
			results.reverse()
	
	return categoryResult, events

def get_results_for_category( series, category ):
	eventResults = []
	for sce in series.seriescompetitionevent_set.all():
		eventResults.extend( extract_event_results(sce) )
	adjust_for_upgrades( series, eventResults )
	
	categories = None
	for g in series.categorygroup_set.all():
		category_pks = set( g.get_category_pk() )
		if category_pk in category_pks:
			categories = set( categories_from_pks(category_pks) )
			break
	if not categories:
		categories = [category]
	eventResults = [rr for rr in eventResults if rr.result.category in categories]
	return [category]
		
