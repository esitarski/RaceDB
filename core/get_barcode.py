import barcode

#----------------------------------------------------------
# EAN 13 encodes a 12-digit number with a 1-digit checksum.
#
nums = '5 9 1 7 6 9 8 3 7 2 1 9 2 5 8 3 9 2 6 5 1 2 7 2 3 4 2 8 9 9 9 1 5 6 8 4 6 6 9 9 1 8 4 6 5 2 8 9 3 8 9 2 2 8 1 5 5 1 3 5 1 4 9 5 8 3 8 1 9 3 9 4 1 3 4 3 5 8 2 3 3 5 9 8 4 5 1 2 6 7 5 2 1 1 1 2 8 9 1 4'
RAND_DIGIT = [int(v) for v in nums.split()[:12]]

def barcode_encode( id ):
	x = RAND_DIGIT
	s = [int(v) for v in '{:012}'.format(id)]
	s.reverse()
	sPrev = 0
	for i in range( 0, 12 ):
		s[i] += sPrev + x[i]
		sPrev += s[i]
	s = s[6:] + s[:6]
	n = int( ''.join('{}'.format(v%10) for v in s) )
	return n

def barcode_validate( s ):
	if len(s) != 13:
		return False
	try:
		s = [int(v) for v in s]
	except ValueError:
		return False
		
	check_digit_given = s.pop()
	sum_even = sum( s[i] for i in range(0, len(s), 2) )
	sum_odd = sum( s[i] for i in range(1, len(s), 2) )
	sum_weighted = sum_even + sum_odd * 3
	check_digit = (10 - sum_weighted % 10) % 10
	
	return check_digit_given == check_digit
	
def barcode_decode( s ):
	s = s[:12]
	try:
		n = int( s )
	except Exception:
		return -1
		
	x = RAND_DIGIT
	s = [int(v) for v in '{:012}'.format(n)]
	s = s[6:] + s[:6]
	sPrev = sum( s )
	for i in range( 11, -1, -1 ):
		sPrev -= s[i]
		s[i] -= sPrev + x[i]
	s.reverse()
	return int( ''.join('{}'.format(v%10) for v in s ) )

def get_barcode( id ):
	return barcode.get( 'ean13', '{:012}'.format(barcode_encode(id)) ).render()

if __name__ == '__main__':
	for id in range(1, 2000):
		n = barcode_encode( id )
		d = barcode_decode( n )
		assert id == d
		print ( id, n, d )
		
	print ( barcode_validate( '1781106520911' ) )
