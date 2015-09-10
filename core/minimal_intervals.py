
def minimal_intervals( numbers ):
	# Input: a list of sets of numbers
	# Output: a set of intervals expressed as [from,to] for each set that are non-intersecting.
	
	def testIntersection( intervalNums, n ):
		return all( nTest.isdisjoint(intervalNums) or n == nTest for nTest in numbers )
	
	intervals = []
	for n in numbers:
		nums = sorted( n )
		intervalCur = []
		while nums:
			left, right = 0, len(nums)
			while right - left > 1:
				mid = left + (right - left) // 2
				if testIntersection( xrange(nums[0], nums[mid]+1), n ):
					left = mid
				else:
					right = mid
			intervalCur.append( (nums[0], nums[left]) )
			nums = nums[left+1:]
		
		intervals.append( intervalCur )

	return intervals
	
def interval_to_str( interval ):
	s = []
	for a, b in interval:
		if a == b:
			s.append( '{}'.format(a) )
		else:
			s.append( '{}-{}'.format(a, b) )
	return ','.join( s )
	
if __name__ == '__main__':
	for i in minimal_intervals( [
					set( [0, 1, 2] ),
					set( [1, 2] ),
					set( x*3 for x in [1,2,3,4,5,7] ),
					set( x*3 for x in [6,8,9,10,11] ),
				]
			):
		print interval_to_str( i )
