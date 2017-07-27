#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import subprocess
import compileall
import platform

is_windows = (platform.system() == 'Windows')

pyllrp = 'pip-install-pyllrp-0.1.4.zip'

dependencies = [
	'django==1.9.9',
	'django-crispy-forms==1.6',
	'django-extensions',
	'requests',
	'dj_static',
	'waitress',
	'xlsxwriter',
	'pygments',
	'xlrd',
	'pytz',
	'fpdf',
	'natural-keys',
	pyllrp,
]

if is_windows:
	dependencies.append('winshell')
	
uninstall_dependencies = [
	'south',
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
	
	# Remove the unecessary TagReadWriteServier directory.
	try:
		shutil.rmtree( 'TagReadWriteServer' )
	except:
		pass
		
	try:
		os.path.remove( os.path.join( 'core', 'migrations', '0002_auto_20150201_1649.py' ) )
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
	
	if is_windows:
		print( 'Creating Windows desktop shortcut...' )
		import CreateShortcut
		CreateShortcut.CreateShortcut()
