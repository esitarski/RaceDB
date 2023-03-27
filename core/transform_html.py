# Script to transform html template files for updates.

import glob

from_to = (
	('date:"Y-m-d"', 			'date_short'),
	('date:"Y-m-d H:i"',		'date_hhmm'),
	('date:"Y-m-d H:i:s"', 		'date_hhmmss'),
	('date:"H:i:s"',			'time_hhmmss'),
	('date:"H:i"',				'time_hhmm'),
)

def transform( fname ):
	with open(fname) as f:
		contents = f.read()
	contents_old = contents
	for s_from, s_to in from_to:
		contents = contents.replace( s_from, s_to )
	if contents_old != contents:
		print( fname, contents )
		with open(fname, 'w') as f:
			f.write( contents )
		
def fix_load( fname ):
	with open(fname) as f:
		contents = f.read()
	if any( s_to in contents for s_from, s_to in from_to ) and '{% load date_fmt %}' not in contents:
		try:
			i = contents.find( '{% load' )
		except:
			return
		contents = contents[:i] + '{% load date_fmt %}\n' + contents[i:]
		print( fname, contents )
		with open(fname, 'w') as f:
			f.write( contents )
	
for fname in glob.glob( 'templates/*.html' ):
	transform( fname )
	fix_load( fname )
