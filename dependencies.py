#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import subprocess
import platform

is_windows = (platform.system() == 'Windows')

def update_dependencies( upgrade ):
	print( 'Updating Dependencies...' )
	
	py = sys.executable
	args = ["pip3", "install", "-r", "requirements.txt"]
	if upgrade:
		args = ["pip3", "install", "--upgrade", "-r", "requirements.txt"]
	print( ' '.join(args) )
	subprocess.call( args )

	print( 'Removing old compiled files...' )
	for root, dirs, files in os.walk( '.' ):
		for f in files:
			fname = os.path.join( root, f )
			if os.path.splitext(fname)[1] == '.pyc':
				os.remove( fname )

if __name__ == '__main__':
	if sys.version_info.major != 3:
		print("Python 3 is required for RaceDB. Please upgrade. Python {}.{} is no longer supported".format(sys.version_info.major, sys.version_info.minor))
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
