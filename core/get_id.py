import os
import random

def get_id( bits = 122 ):
	try:
		v = 0
		for b in os.urandom( (bits >> 3) + int((bits & 7) != 0) ):
			v = (v << 8) | ord(b)
		v &= (1 << bits)-1
	except NotImplementedError:
		v = random.getrandbits( bits )
	
	if not (v & 0xf << (bits-4)):
		v ^= (1 << bits)-1
	return '{:X}'.format( v )
	
	'''
	u = uuid.uuid4()
	i = u.int
	v = '{:0{}X}'.format( i & ((1<<bits)-1), bits//4 )
	return 'F' + v[1:] if v[0] == '0' else v
	'''
	
	
	'''
	u = uuid.uuid1()
	
	node, node_bits		= u.node, 		48
	seq, seq_bits		= u.clock_seq,	14
	time, time_bits		= u.time,		60
	
	if bits < 122:
		# Throw away bits in the sequence and node.
		bits = max( bits, 60 )
		d = 122 - bits
		
		d_seq_bits = (d * seq_bits) // node_bits
		d_node_bits = d - d_seq_bits
		
		node >>= d_node_bits
		node_bits -= d_node_bits
		
		seq >>= d_seq_bits
		seq_bits -= d_seq_bits
	
	return '{:X}'.format( (node << (seq_bits + time_bits)) + (seq << time_bits) + time )
	'''
	
if __name__ == '__main__':
	us = [get_id(96) for i in range(20)]
	for u in us:
		print ( u, len(u) )
