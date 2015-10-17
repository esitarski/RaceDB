import re
import datetime
from collections import defaultdict
import WriteLog

reNonDigits = re.compile('[^0-9]+')
reDigits = re.compile( '[0-9]+' )

epoch = datetime.datetime.utcfromtimestamp(0)
bucketSize = 1*60
def getBucket(dt):
	return int( (dt - epoch).total_seconds() ) // bucketSize

reRemoteAddr = re.compile('remote_addr="([^"]*)"')
rePath = re.compile('path="([^"]*)"')
reUserName = re.compile('username="([^"]*)"')

def parseParameters( s ):
	funcName = None
	participantId = None
	m = rePath.search( s )
	if m:
		pathComponents = m.group(1).split('/')
		try:
			participantId = int( pathComponents[-2] )
		except Exception as e:
			participantId = None
			
		for p in reversed(pathComponents):
			if p and not reDigits.match(p):
				funcName = p
				break
	
	try:
		remoteAddr = reRemoteAddr.search(s).group(1)
	except Exception as e:
		remoteAddr = None
		
	try:
		userName = reUserName.search(s).group(1)
	except Exception as e:
		userName = None
		
	return funcName, remoteAddr, participantId, userName

def AnalyzeLog( logfile = None, start=None, end=None, include_superuser=False ):
	if not logfile:
		logfile = WriteLog.logFileName
		
	# Debug.
	# logfile, start, end = 'core/RaceDBLog.txt', datetime.datetime(2015, 10, 10), datetime.datetime(2015, 10, 11)
	
	errors = []
	
	participantCount = defaultdict( int )
	transactionRateOverTime = defaultdict( int )
	transactionClientRateOverTime = defaultdict( lambda: defaultdict(int) )
	
	functionCount = { fname:0 for fname in [
			'ParticipantCategorySelect', 'ParticipantBibSelect', 'ParticipantTeamSelect',
			'ParticipantPaidChange', 'ParticipantTagChange', 'ParticipantSignatureChange',
		]
	}
	
	with open(logfile, 'r') as f:
		for lineNo, line in enumerate(f):
			line = line.strip()
			if not line:
				continue
			fields = line.split(None, 2)
			
			timestamp = datetime.datetime( *[int(v) for v in reNonDigits.sub(' ', fields[0]).split()] )
			if (start and timestamp < start) or (end and end < timestamp):
				continue
				
			funcName, remoteAddr, participantId, userName = parseParameters( fields[2] )

			if userName == 'super' and not include_superuser:
				continue
			
			if funcName in functionCount:
				functionCount[funcName] += 1
			
			if funcName == 'ParticipantEdit':
				bucket = getBucket( timestamp )
				
				participantCount[participantId] += 1
				transactionRateOverTime[bucket] += 1
				transactionClientRateOverTime[remoteAddr][bucket] += 1
				
	if not transactionRateOverTime:
		return None
	
	bMin = min( b for b in transactionRateOverTime.iterkeys() )
	bMax = max( b for b in transactionRateOverTime.iterkeys() ) + 1
	buckets = [epoch + datetime.timedelta(seconds=b*bucketSize) for b in xrange(bMin, bMax)]
	
	transactionRateOverTime = [transactionRateOverTime[b] for b in xrange(bMin, bMax)]
	tcr = []
	for remote_addr, cp in transactionClientRateOverTime.iteritems():
		tcr.append( (remote_addr, [cp[b] for b in xrange(bMin, bMax)] ) )
	tcr.sort( key=lambda x: (sum(x[1]), x[0]), reverse=True )

	participantTransactionCount = []
	for v in participantCount.itervalues():
		if v >= len(participantTransactionCount):
			participantTransactionCount.extend( [0 for i in xrange(len(participantTransactionCount), v+1)] )
		participantTransactionCount[v] += 1
	total = sum(participantTransactionCount)
	participantTransactionCountPercentage = [(100.0*t) / total for t in participantTransactionCount]

	transactionPeak = [buckets[0], 0]
	for b, p in enumerate(transactionRateOverTime):
		if p > transactionPeak[1]:
			transactionPeak = [buckets[b], p]
			
	functionCount = sorted( ([re.sub('Participant|Select|Change', '', fname), count]
		for fname, count in functionCount.iteritems() if count), key=lambda fc: fc[1], reverse=True )

	return {
		'transactionTotal': total,
		'averageTransactionsPerParticipant': float(sum(participantCount.itervalues())) / float(len(participantCount)),
		'transactionPeak': transactionPeak,
		'transactionRateOverTime': transactionRateOverTime,
		'transactionClientRateOverTime': tcr,
		'participantTransactionCount': participantTransactionCount,
		'participantTransactionCountPercentage': participantTransactionCountPercentage,
		'functionCount': functionCount,
		'functionCountTotal': sum( count for name, count in functionCount ),
		'stations': len(tcr),
		'buckets': [b.strftime('%H:%M').lstrip('0') for b in buckets],
	}
		
if __name__ == '__main__':
	r = AnalyzeLog( 'RaceDBLog.txt', datetime.datetime(2015, 10, 10), datetime.datetime(2015, 10, 11) )
	for k in (	'averageTransactionsPerParticipant', 'participantTransactionCount', 'participantTransactionCountPercentage',
				'stations', 'functionCount'):
		print '{}={}'.format(k, r[k])
	t = r['buckets'][r['transactionPeak'][0]]
	print 'transactionPeak={} at {}-{}'.format(r['transactionPeak'][0], t, t + datetime.timedelta(seconds=bucketSize))
