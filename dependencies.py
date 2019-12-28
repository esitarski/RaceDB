#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import subprocess
import platform
# This isn't really allowed, but its cleaner than running pip by forking a process
from pip._internal.main import main

is_windows = (platform.system() == 'Windows')

uninstall_dependencies = [
	#'south',
]

def update_dependencies( upgrade ):
    print( 'Updating Dependencies...' )

    args = ["install", "-r", "requirements.txt"]
    if upgrade:
        args = ["install", "--upgrade", "-r", "requirements.txt"]
    main(args)

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
