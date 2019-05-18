#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import subprocess
import platform

is_windows = (platform.system() == 'Windows')

pyllrp = 'pip-install-pyllrp-3.0.0.zip'

dependencies = [
	'django',
	'django-crispy-forms',
	'django-extensions',
	'requests',
	'dj_static',
	'waitress',
	'xlsxwriter',
	'xlrd',
	'pytz',
	'tzlocal',
	'fpdf',
	'netifaces',
	pyllrp,
]

uninstall_dependencies = [
	#'south',
]

def update_dependencies( upgrade ):
	print( 'Updating Dependencies...' )
	
	pip = os.path.join( os.path.split(sys.executable)[0], 'pip3' )
	if os.path.isfile(pip):
		print( 'Found "pip" at "{}".'.format(pip) )
	else:
		pip = 'pip3'
	
	for d in dependencies:
		args = [pip, 'install', d]
		if upgrade:
			args.append('--upgrade')
		print( ' '.join(args) )
		subprocess.call( args )

	for d in uninstall_dependencies:
		args = [pip, 'uninstall', d]
		print( ' '.join(args) )
		subprocess.call( args )

	print( 'Removing old compiled files...' )
	for root, dirs, files in os.walk( '.' ):
		for f in files:
			fname = os.path.join( root, f )
			if os.path.splitext(fname)[1] == '.pyc':
				os.remove( fname )

if __name__ == '__main__':
	parser = argparse.ArgumentParser( description='Update RaceDB Dependencies' )
	parser.add_argument(
		'--upgrade',
		action='store_true',
		default=False,
	)
	
	args = parser.parse_args()
	update_dependencies( args.upgrade )
	
	if is_windows:
		print( 'Creating Windows desktop shortcut...' )
		import CreateShortcut
		CreateShortcut.CreateShortcut()
