#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import subprocess
import compileall

pyllrp = 'pip-install-pyllrp-0.1.3.zip'

dependencies = [
	'django==1.8.4',
	'django-crispy-forms==1.5.1',
	'django-extensions',
	'dj_static',
	'waitress',
	'xlsxwriter',
	'xlrd',
	'pytz',
	pyllrp,
]

def update_dependencies( upgrade ):
	print( 'Updating Dependencies...' )
	
	pip = 'C:/Python27/Scripts/pip.exe'
	if os.path.isfile(pip):
		print( 'Found "pip" at "{}".'.format(pip) )
	else:
		pip = 'pip'
	
	for d in dependencies:
		args = [pip, 'install', d]
		if upgrade:
			args.append('--upgrade')
		print( ' '.join(args) )
		subprocess.call( args )

	print( 'Removing old compiled files...' )
	for root, dirs, files in os.walk( '.' ):
		for f in files:
			fname = os.path.join( root, f )
			if os.path.splitext(fname)[1] == '.pyc':
				os.remove( fname )
	
	# Remove the unecessary TagReadWriteServier directory.
	try:
		shutil.rmtree( 'TagReadWriteServer' )
	except:
		pass
		
	print( 'Pre-compiling source code...' )
	compileall.compile_dir( '.', quiet=True )

if __name__ == '__main__':
	parser = argparse.ArgumentParser( description='Update RaceDB Dependencies' )
	parser.add_argument(
		'--upgrade',
		action='store_true',
		default=False,
	)
	
	args = parser.parse_args()
	update_dependencies( args.upgrade )
