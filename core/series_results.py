from models import *

import os
import math
import operator
import datetime
import itertools
import random
from copy import deepcopy

import utils
from collections import defaultdict
from django.utils.safestring import mark_safe

ordinal = lambda n: "{}{}".format(n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

class EventResult( object ):

	__slots__ = ('status', 'participant', 'license_holder', 'event', 'rank', 'starters', 'value_for_rank', 'category', 'original_category', 'ignored')
	
	def __init__( self, result, rank, starters, value_for_rank ):
		self.status = result.status
		self.participant = result.participant
		self.license_holder = result.participant.license_holder
		self.event = result.event
		
		self.rank = rank
		self.starters = starters
		
		self.value_for_rank = value_for_rank
		self.original_category = self.category = result.participant.category
		
		self.ignored = False
		
	@property
	def upgraded( self ):
		return self.category != self.original_category
		
	@property
	def team_name( self ):
		team = self.participant.team
		return team.name if team else u''
		
	@property
	def status_rank( self ):
		return self.rank if self.status == 0 else 999999
	
	@property
	def rank_text( self ):
		if self.status != Result.cFinisher:
			return next(v for v in Result.STATUS_CODE_NAMES if v[0] == self.status)[1]
		return ordinal( self.rank )

def extract_event_results( sce, filter_categories=None, filter_license_holders=None ):
	series = sce.series
	
	if not filter_categories:
		filter_categories = series.get_categories()
		
	if filter_license_holders and not isinstance(filter_license_holders, set):
		filter_license_holders = set( filter_license_holders )
	
	if not isinstance(filter_categories, set):
		filter_categories = set( filter_categories )
	
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
	
	if get_points:
		def get_value_for_rank( rr, rank, rrWinner ):
			return get_points( rank, rr.status )
	elif series.ranking_criteria == 1:	# Time
		def get_value_for_rank( rr, rank, rrWinner ):
			try:
				return rr.finish_time.total_seconds()
			except:
				return 24.0*60.0*60.0
	elif series.ranking_criteria == 2:	# % Winner / Time
		def get_value_for_rank( rr, rank, rrWinner ):
			try:
				return 100.0 * rrWinner.finish_time.total_seconds() / rr.finish_time.total_seconds()
			except:
				return 0
	else:
		assert False, 'Unknown ranking criteria'
	
	eventResults = []
	for w in sce.event.get_wave_set().all():
		if filter_categories.isdisjoint( w.categories.all() ):
			continue
			
		if w.rank_categories_together:
			get_rank     = lambda rr: rr.wave_rank
			get_starters = lambda rr: rr.wave_starters
		else:
			get_rank     = lambda rr: rr.category_rank
			get_starters = lambda rr: rr.category_starters
	
		rr_winner = None
		wave_results = w.get_results().filter( status__in=status_keep, participant__category__in=filter_categories )
		wave_results = wave_results.prefetch_related('participant', 'participant__license_holder', 'participant__category', 'participant__team').order_by('wave_rank')
		for rr in wave_results:
			if w.rank_categories_together:
				if not rr_winner:
					rr_winner = rr
			else:
				if not rr_winner or rr_winner.participant.category != rr.participant.category:
					rr_winner = rr

			if filter_license_holders and rr.participant.license_holder not in filter_license_holders:
				continue
				
			rank = get_rank( rr )
			value_for_rank = get_value_for_rank(rr, rank, rr_winner)
			if value_for_rank:
				eventResults.append( EventResult(rr, rank, get_starters(rr), value_for_rank) )

	return eventResults

def adjust_for_upgrades( series, eventResults ):
	if series.ranking_criteria != 0:
		return

	has_zero_factor = False
	upgradeCategoriesAll = set()
	factorPathPositions = []
	for sup in series.seriesupgradeprogression_set.all():
		if sup.factor == 0.0:
			has_zero_factor = True
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
			
			highestPos, highestCategory = -1, None
			for cat in upgradeCategories.iterkeys():
				pos = position[cat]
				if pos > highestPos:
					highestPos, highestCategory = pos, cat
		
			for cat, rrs in upgradeCategories.iteritems():
				if cat == highestCategory:
					continue
				power = highestPos - position[cat]
				for rr in rrs:
					rr.category = highestCategory
					rr.value_for_rank *= (factor ** power)
		
			break

	# Remove any trace of previous results if the factor was zero.
	if has_zero_factor:
		eventResults[:] = [rr for rr in eventResults if rr.value_for_rank > 0.0]
		
def series_results( series, categories, eventResults ):
	scoreByTime = (series.ranking_criteria == 1)
	scoreByPercent = (series.ranking_criteria == 2)
	bestResultsToConsider = series.best_results_to_consider
	mustHaveCompleted = series.must_have_completed
	showLastToFirst = series.show_last_to_first
	considerMostEventsCompleted = series.consider_most_events_completed
	numPlacesTieBreaker = series.tie_breaking_rule
	
	# Get all results for this category.
	categories = set( list(categories) )
	eventResults = [rr for rr in eventResults if rr.category in categories]
	if not eventResults:
		return [], []
	eventResults.sort( key=operator.attrgetter('event.date_time', 'event.name', 'rank') )
	
	# Assign a sequence number to the events.
	events = sorted( set(rr.event for rr in eventResults), key=operator.attrgetter('date_time') )
	eventSequence = {e:i for i, e in enumerate(events)}
	
	lhEventsCompleted = defaultdict( int )
	lhPlaceCount = defaultdict( lambda : defaultdict(int) )
	lhTeam = defaultdict( unicode )
		
	lhResults = defaultdict( lambda : [None] * len(events) )
	lhFinishes = defaultdict( lambda : [None] * len(events) )
	
	lhValue = defaultdict( float )
	
	percentFormat = u'{:.2f}'
	floatFormat = u'{:0.2f}'
	
	# Get the individual results for each lh, and the total value.
	for rr in eventResults:
		lh = rr.license_holder
		lhTeam[lh] = rr.participant.team.name if rr.participant.team else u''
		lhResults[lh][eventSequence[rr.event]] = rr
		lhValue[lh] += rr.value_for_rank
		lhPlaceCount[lh][rr.rank] += 1
		lhEventsCompleted[lh] += 1
	
	# Remove if minimum events not completed.
	lhOrder = [lh for lh, results in lhResults.iteritems() if lhEventsCompleted[lh] >= mustHaveCompleted]
	
	# Adjust for the best results.
	if bestResultsToConsider > 0:
		for lh, rrs in lhResults.iteritems():
			iResults = [(i, rr) for i, rr in enumerate(rrs) if rr is not None]
			if len(iResults) > bestResultsToConsider:
				if scoreByTime:
					iResults.sort( key=(lambda x: x[1].value_for_rank, x[0]) )
				else:
					iResults.sort( key=(lambda x: -x[1].value_for_rank, x[0]) )
				for i, t in iResults[bestResultsToConsider:]:
					lhValue[lh] -= t
					rrs[i].ignored = True
				lhEventsCompleted[lh] = bestResultsToConsider

	lhGap = {}
	if scoreByTime:
		# Sort by decreasing events completed, then increasing time.
		lhOrder.sort( key = lambda r: tuple(itertools.chain(
				[-lhEventsCompleted[r], lhValue[r]],
				[-lhPlaceCount[r][k] for k in xrange(1, numPlacesTieBreaker+1)],
				[rr.status_rank if rr else 9999999 for rr in reversed(lhResults[r])]
			))
		)
		# Compute the time gap.
		if lhOrder:
			leader = lhOrder[0]
			leaderValue = lhValue[leader]
			leaderEventsCompleted = lhEventsCompleted[leader]
			lhGap = { r : lhValue[r] - leaderValue if lhEventsCompleted[r] == leaderEventsCompleted else None for r in lhOrder }
	
	else:
		# Sort by decreasing value.
		lhOrder.sort( key = lambda r: tuple(itertools.chain(
				[-lhValue[r]],
				([-lhEventsCompleted[r]] if considerMostEventsCompleted else []),
				[-lhPlaceCount[r][k] for k in xrange(1, numPlacesTieBreaker+1)],
				[rr.status_rank if rr else 9999999 for rr in reversed(lhResults[r])]
			))
		)
		
		# Compute the gap.
		lhGap = {}
		if lhOrder:
			leader = lhOrder[0]
			leaderValue = lhValue[leader]
			lhGap = { r : leaderValue - lhValue[r] for r in lhOrder }
				
	# List of:
	# license_holder, team, totalValue, gap, [list of results for each event in series]
	categoryResult = [[lh, lhTeam[lh], lhValue[lh], lhGap[lh]] + [lhResults[lh]] for lh in lhOrder]
	if showLastToFirst:
		events.reverse()
		for lh, team, value, gap, results in categoryResult:
			results.reverse()
	
	return categoryResult, events

def get_results_for_category( series, category ):
	related_categories = series.get_related_categories( category )
	
	eventResults = []
	for sce in series.seriescompetitionevent_set.all():
		eventResults.extend( extract_event_results(sce, related_categories) )
	adjust_for_upgrades( series, eventResults )
	
	return series_results( series, series.get_group_related_categories(category), eventResults )

def get_callups_for_wave( series, wave, eventResultsAll=None ):
	event = wave.event
	competition = event.competition
	RC = event.get_result_class()
	
	randomize = series.randomize_if_no_results
	
	series_categories = set( series.get_categories() )
	participants = set( wave.get_participants_unsorted().exclude(bib__isnull=True).select_related('license_holder') )
	license_holders = set( p.license_holder for p in participants )
	p_from_lh = {p.license_holder:p for p in participants}

	callups = []
	
	FakeFinishValue = 1.0
	
	categories_seen = set()
	for c in wave.categories.all():
		if c in categories_seen:
			continue
		group_categories = set( series.get_group_related_categories(c) )
		categories_seen |= group_categories
		
		related_categories = series.get_related_categories( c )
	
		if eventResultsAll:
			eventResults = [deepcopy(er) for er in eventResultsAll if er.license_holder in license_holders]
		else:
			eventResults = []
			for sce in series.seriescompetitionevent_set.all():
				if sce.event.date_time < event.date_time:
					eventResults.extend( extract_event_results(sce, related_categories, license_holders) )					
		
		# Add "fake" Results for all participants in the current event with 1.0 as value_for_rank.
		fakeResult = RC( event=event, status=0 )
		for p in participants:
			if p.category in series_categories and p.category in group_categories:
				fakeResult.participant = p
				eventResults.append( EventResult(fakeResult, 1, 1, FakeFinishValue) )

		# The fake results ensure any upgraded athletes's points will be considered properly if this is their first upgraded race.
		adjust_for_upgrades( series, eventResults )
		
		# Compute the series standings.
		categoryResult, events = series_results( series, group_categories, eventResults )
		
		# Remove entries beyond the callup max.
		del categoryResult[series.callup_max:]
		
		# Get the values we need and subtract for the FakeFinishValue.
		p_values = [[p_from_lh[lh], value-FakeFinishValue] for lh, team, value, gap, results in categoryResult]
			
		# Return the participant and the points value.
		if randomize:
			# Randomize athletes with no results.
			random.seed( (competition.id, series.id, c.id, wave.id) )
			for p_start, (p, value) in enumerate(p_values):
				if value == 0.0:
					r = p_values[p_start:]
					random.shuffle( r )
					p_values[p_start:] = r
					break
		else:
			# Remove athletes with no results.
			p_values = [[p, value] for p, value in p_values if value]
		
		if p_values:
			callups.append( (
					sorted(group_categories, key=operator.attrgetter('sequence')),
					p_values,
				)
			)
	
	# Returns a list of tuples (list of categories, list of (participants, points))
	return callups

