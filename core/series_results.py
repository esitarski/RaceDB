from models import *

import os
import math
import datetime
import operator
from collections import defaultdict

#import trueskill

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

def safe_upper( f ):
	try:
		return f.upper()
	except:
		return f

class EventResult( object ):
	rankDNF = 999998
	rankDNS = 999999
	
	def __init__( self, result, rank, tFinish=None, tProjected=None ):
		self.result = result
		self.rank = rank
		self.category = rank.participant.category
		
		self.tFinish = tFinish
		self.tProjected = tProjected if tProjected else tFinish
		
		self.upgradeFactor = 1
		self.upgradeResult = False
			
	def keySort( self ):
		return tuple( self.category.sequence, self.rank.participant.license_holder.search_text, self.result.event.date_time )
		
	def keyMatch( self ):
		return tuple( self.category, self.rank.participant.license_holder )
		
	def key( self ):
		return self.rank.participant.license_holder

def toInt( n ):
	if n == 'DNF':
		return EventResult.rankDNF
	if n == 'DNS':
		return EventResult.rankDNS
	
	try:
		return int(n.split()[0])
	except:
		return n

def extract_event_results( sce ):
	series = sce.series
	
	points_structure = sce.points_structure if series.ranking_criteria == 0 else None
	status_keep = [Result.cFinisher, Result.cPUL]
	if points_structure:
		if points_structure.dnf_points:
			status_keep.append( Result.cDNF )
		if points_structure.dnf_points:
			status_keep.append( Result.cDNS )
	
	def get_rank( w, rr ):
		if rr.status in (Result.cDNF, Result.cOTB):
			return EventResult.RankDNF
		elif rr.status == Result.cDNS:
			return EventResult.RankDNS
		if w.rank_categories_together:
			return rr.wave_rank
		else:
			return rr.category_rank
	
	eventResults = []
	for w in sce.event.get_wave_set().all():
		for rr in w.get_results().filter(
				participant__category__in=series.get_category_pk() ).filter(
				status__in=status_keep ).select_related(
				'participant', 'participant__license_holder'
			):
			eventResults.append( EventResult(rr, get_rank(w, rr), rr.finish_time) )

	return eventResults

def AdjustForUpgrades( eventResults ):
	upgradePaths = []
	for path in SeriesModel.model.upgradePaths:
		upgradePaths.append( [p.strip() for p in path.split(',')] )
	upgradeFactors = SeriesModel.model.upgradeFactors
	
	competitionCategories = defaultdict( lambda: defaultdict(list) )
	for rr in eventResults:
		competitionCategories[rr.key()][rr.categoryName].append( rr )
	
	for key, categories in competitionCategories.iteritems():
		if len(categories) == 1:
			continue
		
		for i, path in enumerate(upgradePaths):
			upgradeCategories = { cName: rrs for cName, rrs in categories.iteritems() if cName in path }
			if len(upgradeCategories) <= 1:
				continue
			
			try:
				upgradeFactor = upgradeFactors[i]
			except:
				upgradeFactor = 0.5
			
			categoryPosition = {}
			highestCategoryPosition, highestCategoryName = -1, None
			for cName in upgradeCategories.iterkeys():
				pos = path.index( cName )
				categoryPosition[cName] = pos
				if pos > highestCategoryPosition:
					highestCategoryPosition, highestCategoryName = pos, cName
			
			for cName, rrs in upgradeCategories.iteritems():
				for rr in rrs:
					if rr.categoryName != highestCategoryName:
						rr.categoryName = highestCategoryName
						rr.upgradeFactor = upgradeFactor ** (highestCategoryPosition - categoryPosition[cName])
						rr.upgradeResult = True
		
			break

def GetCategoryResults( categoryName, eventResults, pointsForRank, useMostEventsCompleted=False, numPlacesTieBreaker=5 ):
	scoreByTime = SeriesModel.model.scoreByTime
	scoreByPercent = SeriesModel.model.scoreByPercent
	scoreByTrueSkill = SeriesModel.model.scoreByTrueSkill
	bestResultsToConsider = SeriesModel.model.bestResultsToConsider
	mustHaveCompleted = SeriesModel.model.mustHaveCompleted
	showLastToFirst = SeriesModel.model.showLastToFirst
	considerPrimePointsOrTimeBonus = SeriesModel.model.considerPrimePointsOrTimeBonus
	
	# Get all results for this category.
	eventResults = [rr for rr in eventResults if rr.categoryName == categoryName]
	if not eventResults:
		return [], [], set()
		
	# Assign a sequence number to the races in the specified order.
	for i, r in enumerate(SeriesModel.model.races):
		r.iSequence = i
		
	# Get all races for this category.
	races = set( (rr.raceDate, rr.raceName, rr.raceURL, rr.raceInSeries) for rr in eventResults )
	races = sorted( races, key = lambda r: r[3].iSequence )
	raceSequence = dict( (r[3], i) for i, r in enumerate(races) )
	
	riderEventsCompleted = defaultdict( int )
	riderPlaceCount = defaultdict( lambda : defaultdict(int) )
	riderTeam = defaultdict( lambda : u'' )
	riderUpgrades = defaultdict( lambda : [False] * len(races) )
	riderNameLicense = {}
	
	def asInt( v ):
		return int(v) if int(v) == v else v
	
	ignoreFormat = u'[{}**]'
	upgradeFormat = u'{} pre-upg'
	
	def FixUpgradeFormat( riderUpgrades, riderResults ):
		# Format upgrades so they are visible in the results.
		for rider, upgrades in riderUpgrades.iteritems():
			for i, u in enumerate(upgrades):
				if u:
					v = riderResults[rider][i]
					riderResults[rider][i] = tuple([upgradeFormat.format(v[0] if v[0] else '')] + list(v[1:]))
	
	riderResults = defaultdict( lambda : [(0,0,0,0)] * len(races) )
	riderFinishes = defaultdict( lambda : [None] * len(races) )
	if scoreByTime:
		# Get the individual results for each rider, and the total time.  Do not consider DNF riders as they have invalid times.
		eventResults = [rr for rr in eventResults if rr.rank != EventResult.rankDNF]
		riderTFinish = defaultdict( float )
		for rr in eventResults:
			try:
				tFinish = float(rr.tFinish - (rr.timeBonus if considerPrimePointsOrTimeBonus else 0.0))
			except ValueError:
				continue
			rider = rr.key()
			riderNameLicense[rider] = (rr.full_name, rr.license)
			if rr.team and rr.team != u'0':
				riderTeam[rider] = rr.team
			riderResults[rider][raceSequence[rr.raceInSeries]] = (
				formatTime(tFinish, True), rr.rank, 0, rr.timeBonus if considerPrimePointsOrTimeBonus else 0.0
			)
			riderFinishes[rider][raceSequence[rr.raceInSeries]] = tFinish
			riderTFinish[rider] += tFinish
			riderUpgrades[rider][raceSequence[rr.raceInSeries]] = rr.upgradeResult
			riderPlaceCount[rider][rr.rank] += 1
			riderEventsCompleted[rider] += 1

		# Adjust for the best times.
		if bestResultsToConsider > 0:
			for rider, finishes in riderFinishes.iteritems():
				iTimes = [(i, t) for i, t in enumerate(finishes) if t is not None]
				if len(iTimes) > bestResultsToConsider:
					iTimes.sort( key=operator.itemgetter(1, 0) )
					for i, t in iTimes[bestResultsToConsider:]:
						riderTFinish[rider] -= t
						v = riderResults[rider][i]
						riderResults[rider][i] = tuple([ignoreFormat.format(v[0])] + list(v[1:]))
					riderEventsCompleted[rider] = bestResultsToConsider

		# Filter out minimal events completed.
		riderOrder = [rider for rider, results in riderResults.iteritems() if riderEventsCompleted[rider] >= mustHaveCompleted]
		
		# Sort by decreasing events completed, then increasing rider time.
		riderOrder.sort( key = lambda r: (-riderEventsCompleted[r], riderTFinish[r]) )
		
		# Compute the time gap.
		riderGap = {}
		if riderOrder:
			leader = riderOrder[0]
			leaderTFinish = riderTFinish[leader]
			leaderEventsCompleted = riderEventsCompleted[leader]
			riderGap = { r : riderTFinish[r] - leaderTFinish if riderEventsCompleted[r] == leaderEventsCompleted else None for r in riderOrder }
			riderGap = { r : formatTimeGap(gap) if gap else u'' for r, gap in riderGap.iteritems() }
		
		# List of:
		# lastName, firstName, license, team, tTotalFinish, [list of (points, position) for each race in series]
		categoryResult = [list(riderNameLicense[rider]) + [riderTeam[rider], formatTime(riderTFinish[rider],True), riderGap[rider]] + [riderResults[rider]] for rider in riderOrder]
		return categoryResult, races, GetPotentialDuplicateFullNames(riderNameLicense)
	
	elif scoreByPercent:
		# Get the individual results for each rider as a percentage of the winner's time.  Ignore DNF riders.
		eventResults = [rr for rr in eventResults if rr.rank != EventResult.rankDNF]

		percentFormat = u'{:.2f}'
		riderPercentTotal = defaultdict( float )
		
		raceLeader = { rr.raceInSeries: rr for rr in eventResults if rr.rank == 1 }
		
		for rr in eventResults:
			tFastest = raceLeader[rr.raceInSeries].tProjected
			
			try:
				tFinish = rr.tProjected
			except ValueError:
				continue
			rider = rr.key()
			riderNameLicense[rider] = (rr.full_name, rr.license)
			if rr.team and rr.team != u'0':
				riderTeam[rider] = rr.team
			percent = min( 100.0, (tFastest / tFinish) * 100.0 if tFinish > 0.0 else 0.0 ) * (rr.upgradeFactor if rr.upgradeResult else 1)
			riderResults[rider][raceSequence[rr.raceInSeries]] = (
				u'{}, {}'.format(percentFormat.format(percent), formatTime(tFinish, False)), rr.rank, 0, 0
			)
			riderFinishes[rider][raceSequence[rr.raceInSeries]] = percent
			riderPercentTotal[rider] += percent
			riderUpgrades[rider][raceSequence[rr.raceInSeries]] = rr.upgradeResult
			riderPlaceCount[rider][rr.rank] += 1
			riderEventsCompleted[rider] += 1

		# Adjust for the best percents.
		if bestResultsToConsider > 0:
			for rider, finishes in riderFinishes.iteritems():
				iPercents = [(i, p) for i, p in enumerate(finishes) if p is not None]
				if len(iPercents) > bestResultsToConsider:
					iPercents.sort( key=lambda x: (-x[1], x[0]) )
					for i, p in iPercents[bestResultsToConsider:]:
						riderPercentTotal[rider] -= p
						v = riderResults[rider][i]
						riderResults[rider][i] = tuple([ignoreFormat.format(v[0])] + list(v[1:]))

		# Filter out minimal events completed.
		riderOrder = [rider for rider, results in riderResults.iteritems() if riderEventsCompleted[rider] >= mustHaveCompleted]
		
		# Sort by decreasing percent total.
		riderOrder.sort( key = lambda r: -riderPercentTotal[r] )
		
		# Compute the points gap.
		riderGap = {}
		if riderOrder:
			leader = riderOrder[0]
			leaderPercentTotal = riderPercentTotal[leader]
			riderGap = { r : leaderPercentTotal - riderPercentTotal[r] for r in riderOrder }
			riderGap = { r : percentFormat.format(gap) if gap else u'' for r, gap in riderGap.iteritems() }
					
		# List of:
		# lastName, firstName, license, team, totalPercent, [list of (percent, position) for each race in series]
		categoryResult = [list(riderNameLicense[rider]) + [riderTeam[rider], percentFormat.format(riderPercentTotal[rider]), riderGap[rider]] + [riderResults[rider]] for rider in riderOrder]
		return categoryResult, races, GetPotentialDuplicateFullNames(riderNameLicense)
	
	elif scoreByTrueSkill:
		# Get an intial Rating for all riders.
		tsEnv = trueskill.TrueSkill( draw_probability=0.0 )
		
		sigmaMultiple = 3.0
		
		def formatRating( rating ):
			return u'{:0.2f} ({:0.2f},{:0.2f})'.format(
				rating.mu-sigmaMultiple*rating.sigma,
				rating.mu,
				rating.sigma
			)
	
		# Get the individual results for each rider, and the total points.
		riderRating = {}
		riderPoints = defaultdict( int )
		for rr in eventResults:
			rider = rr.key()
			riderNameLicense[rider] = (rr.full_name, rr.license)
			if rr.team and rr.team != u'0':
				riderTeam[rider] = rr.team
			if rr.rank != EventResult.rankDNF:
				riderResults[rider][raceSequence[rr.raceInSeries]] = (0, rr.rank, 0, 0)
				riderFinishes[rider][raceSequence[rr.raceInSeries]] = rr.rank
				riderPlaceCount[rider][rr.rank] += 1

		riderRating = { rider:tsEnv.Rating() for rider in riderResults.iterkeys() }
		for iRace in xrange(len(races)):
			# Get the riders that participated in this race.
			riderRank = sorted(
				((rider, finishes[iRace]) for rider, finishes in riderFinishes.iteritems() if finishes[iRace] is not None),
				key=operator.itemgetter(1)
			)
			
			if len(riderRank) <= 1:
				continue
			
			# Update the ratings based on this race's outcome.
			# The TrueSkill rate function requires each rating to be a list even if there is only one.
			ratingNew = tsEnv.rate( [[riderRating[rider]] for rider, rank in riderRank] )
			riderRating.update( {rider:rating[0] for (rider, rank), rating in zip(riderRank, ratingNew)} )
			
			# Update the partial results.
			for rider, rank in riderRank:
				rating = riderRating[rider]
				riderResults[rider][iRace] = (formatRating(rating), rank, 0, 0)

		# Assign rider points based on mu-3*sigma.
		riderPoints = { rider:rating.mu-sigmaMultiple*rating.sigma for rider, rating in riderRating.iteritems() }
		
		# Sort by rider points - greatest number of points first.
		riderOrder = sorted( riderPoints.iterkeys(), key=lambda r: riderPoints[r], reverse=True )

		# Compute the points gap.
		riderGap = {}
		if riderOrder:
			leader = riderOrder[0]
			leaderPoints = riderPoints[leader]
			riderGap = { r : leaderPoints - riderPoints[r] for r in riderOrder }
			riderGap = { r : u'{:0.2f}'.format(gap) if gap else u'' for r, gap in riderGap.iteritems() }
		
		riderPoints = { rider:formatRating(riderRating[rider]) for rider, points in riderPoints.iteritems() }
		
		# Reverse the race order if required.
		if showLastToFirst:
			races.reverse()
			for results in riderResults.itervalues():
				results.reverse()
		
		# List of:
		# lastName, firstName, license, team, points, [list of (points, position) for each race in series]
		categoryResult = [list(riderNameLicense[rider]) + [riderTeam[rider], riderPoints[rider], riderGap[rider]] + [riderResults[rider]] for rider in riderOrder]
		return categoryResult, races, GetPotentialDuplicateFullNames(riderNameLicense)
		
	else:
		# Get the individual results for each rider, and the total points.
		riderPoints = defaultdict( int )
		for rr in eventResults:
			rider = rr.key()
			riderNameLicense[rider] = (rr.full_name, rr.license)
			if rr.team and rr.team != u'0':
				riderTeam[rider] = rr.team
			primePoints = rr.primePoints if considerPrimePointsOrTimeBonus else 0
			earnedPoints = pointsForRank[rr.raceFileName][rr.rank] + primePoints
			points = asInt( earnedPoints * rr.upgradeFactor )
			riderResults[rider][raceSequence[rr.raceInSeries]] = (points, rr.rank, primePoints, 0)
			riderFinishes[rider][raceSequence[rr.raceInSeries]] = points
			riderPoints[rider] += points
			riderPoints[rider] = asInt( riderPoints[rider] )
			riderUpgrades[rider][raceSequence[rr.raceInSeries]] = rr.upgradeResult
			riderPlaceCount[rider][rr.rank] += 1
			riderEventsCompleted[rider] += 1

		# Adjust for the best scores.
		if bestResultsToConsider > 0:
			for rider, finishes in riderFinishes.iteritems():
				iPoints = [(i, p) for i, p in enumerate(finishes) if p is not None]
				if len(iPoints) > bestResultsToConsider:
					iPoints.sort( key=lambda x: (-x[1], x[0]) )
					for i, p in iPoints[bestResultsToConsider:]:
						riderPoints[rider] -= p
						v = riderResults[rider][i]
						riderResults[rider][i] = tuple([ignoreFormat.format(v[0] if v[0] else '')] + list(v[1:]))

		FixUpgradeFormat( riderUpgrades, riderResults )

		# Filter out minimal events completed.
		riderOrder = [rider for rider, results in riderResults.iteritems() if riderEventsCompleted[rider] >= mustHaveCompleted]
		
		# Sort by rider points - greatest number of points first.  Break ties with place count, then
		# most recent result.
		iRank = 1
		riderOrder.sort(key = lambda r:	[riderPoints[r]] +
										([riderEventsCompleted[r]] if useMostEventsCompleted else []) +
										[riderPlaceCount[r][k] for k in xrange(1, numPlacesTieBreaker+1)] +
										[-rank for points, rank, primePoints, timeBonus in riderResults[r]],
						reverse = True )
		
		# Compute the points gap.
		riderGap = {}
		if riderOrder:
			leader = riderOrder[0]
			leaderPoints = riderPoints[leader]
			riderGap = { r : leaderPoints - riderPoints[r] for r in riderOrder }
			riderGap = { r : unicode(gap) if gap else u'' for r, gap in riderGap.iteritems() }
		
		# Reverse the race order if required.
		if showLastToFirst:
			races.reverse()
			for results in riderResults.itervalues():
				results.reverse()
		
		# List of:
		# lastName, firstName, license, team, points, [list of (points, position) for each race in series]
		categoryResult = [list(riderNameLicense[rider]) + [riderTeam[rider], riderPoints[rider], riderGap[rider]] + [riderResults[rider]] for rider in riderOrder]
		return categoryResult, races, GetPotentialDuplicateFullNames(riderNameLicense)

