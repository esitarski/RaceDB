import os
import random

def get_id( bits = 122 ):
	try:
		v = 0
		for b in os.urandom( (bits >> 3) + int((bits & 7) != 0) ):
			v = (v << 8) | b
		v &= (1 << bits)-1
	except NotImplementedError:
		v = random.getrandbits( bits )
	
	if not (v & 0xf << (bits-4)):
		v ^= (1 << bits)-1
	return '{:X}'.format( v )
	
if __name__ == '__main__':
	us = [get_id(96) for i in range(20)]
	for u in us:
		print ( u, len(u) )
