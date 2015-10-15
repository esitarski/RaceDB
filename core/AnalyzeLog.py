
import re
import datetime
from collections import defaultdict

reNonDigits = re.compile('[^0-9]+')

epoch = datetime.datetime.utcfromtimestamp(0)
bucketSize = 1*60
def getBucket(dt):
	return int( (dt - epoch).total_seconds() + 0.5 ) // bucketSize

reRemoteAddr = re.compile('remote_addr="([^"]*)"')
rePath = re.compile('path="([^"]*)"')
reUserName = re.compile('username="([^"]*)"')
def parseParameters( s ):
	remoteAddr, participantId, userName = None, None, None
	
	m = reRemoteAddr.search( s )
	if m:
		remoteAddr = m.group(1)
		
	m = rePath.search( s )
	if m:
		try:
			participantId = int( m.group(1).split('/')[-2] )
		except Exception as e:
			pass
	
	m = reUserName.search( s )
	if m:
		userName = m.group(1)
		
	return remoteAddr, participantId, userName

def AnalyzeLog( logfile, start=None, end=None, include_superuser=False ):
	errors = []
	
	participantCount = defaultdict( int )
	transactionProfile = defaultdict( int )
	transactionClientProfile = defaultdict( lambda: defaultdict(int) )
	
	functionCount = { fname:0 for fname in [
			'ParticipantCategorySelect', 'ParticipantBibSelect', 'ParticipantTeamSelect',
			'LicenseHolderConfirmAddToCompetition', 'ParticipantPaidChange',
			'LicenseHolderNew', 'ParticipantTagChange'
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
				
			func = fields[2]
			remoteAddr, participantId, userName = parseParameters( func )
			print timestamp, remoteAddr, participantId, userName

			if not include_superuser and userName == 'super':
				continue
			
			funcName = func.split( '(', 1 )[0]
			if funcName in functionCount:
				functionCount[funcName] += 1
			
			if func.startswith( 'ParticipantEdit(' ):			
				bucket = getBucket( timestamp )
				
				participantCount[participantId] += 1
				transactionProfile[bucket] += 1
				transactionClientProfile[remoteAddr][bucket] += 1
				
	if not transactionProfile:
		return None
	
	bMin = min( b for b in transactionProfile.iterkeys() )
	bMax = max( b for b in transactionProfile.iterkeys() ) + 1
	print bMin, bMax
	buckets = [epoch + datetime.timedelta(seconds=b*bucketSize) for b in xrange(bMin, bMax)]
	
	transactionProfile = [transactionProfile[b] for b in xrange(bMin, bMax)]
	tpc = []
	for remote_addr, cp in transactionClientProfile.iteritems():
		tpc.append( (remote_addr, [cp[b] for b in xrange(bMin, bMax)] ) )
	tpc.sort()

	transactionFrequency = []
	for v in participantCount.itervalues():
		if v >= len(transactionFrequency):
			transactionFrequency.extend( [0 for i in xrange(len(transactionFrequency), v+1)] )
		transactionFrequency[v] += 1
	total = sum(transactionFrequency)
	transactionFrequencyPercentage = [(100.0*t) / total for t in transactionFrequency]

	transactionPeak = (0, 0)
	for b, p in enumerate(transactionProfile):
		if p > transactionPeak[1]:
			transactionPeak = (b, p)
			
	averageTransationRate = sum(transactionProfile) / float(bMax - bMin)
	
	functionCount = sorted( ((fname, count) for fname, count in functionCount.iteritems()), key=lambda fc: fc[1], reverse=True )

	return {
		'buckets': buckets,
		'functionCount': functionCount,
		'transactionPeak': transactionPeak,
		'averageTransationRate': averageTransationRate,
		'transactionProfile': transactionProfile,
		'transactionClientProfile': tpc,
		'participantCount': participantCount,
		'averageTransactionsPerParticipant': float(sum(participantCount.itervalues())) / float(len(participantCount)),
		'transactionFrequency': transactionFrequency,
		'transactionFrequencyPercentage': transactionFrequencyPercentage,
		'workstations': len(tpc),
	}
		
if __name__ == '__main__':
	r = AnalyzeLog( 'RaceDBLog.txt', datetime.datetime(2015, 10, 10), datetime.datetime(2015, 10, 11) )
	for k in (	'averageTransactionsPerParticipant', 'transactionFrequency', 'transactionFrequencyPercentage',
				'workstations', 'averageTransationRate', 'functionCount'):
		print '{}={}'.format(k, r[k])
	t = r['buckets'][r['transactionPeak'][0]]
	print 'transactionPeak={} at {}-{}'.format(r['transactionPeak'][0], t, t + datetime.timedelta(seconds=bucketSize))
