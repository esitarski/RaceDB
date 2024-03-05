#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
import platform

is_windows = (platform.system() == 'Windows')

def update_dependencies( upgrade ):
	pip_cmd = 'pip3'
	
	print( 'Updating Dependencies...' )
	
	if upgrade:
		args = [pip_cmd, "install", "--upgrade", "-r", "requirements.txt"]
	else:
		args = [pip_cmd, "install", "-r", "requirements.txt"]
	print( ' '.join(args) )
	subprocess.call( args )

	print( 'Removing old compiled files...' )
	for root, dirs, files in os.walk( '.' ):
		for f in files:
			fname = os.path.join( root, f )
			if os.path.splitext(fname)[1] == '.pyc':
				os.remove( fname )

if __name__ == '__main__':
	python_min = (3,7)
	if sys.version_info[:len(python_min)] < python_min:
		print("Python {} or later is required for RaceDB. Please upgrade".format(python_min))
		sys.exit(1)
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
