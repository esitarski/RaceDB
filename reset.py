#!/usr/bin/env python 

import os, fnmatch

def remove_pyc( directory = '.', pattern = '*.pyc' ):
	for root, dirs, files in os.walk(directory):
		for basename in files:
			if fnmatch.fnmatch(basename, pattern):
				fname = os.path.join(root, basename)
				print ( fname )
				os.remove( os.path.join(root, basename) )
				
if __name__ == '__main__':
	remove_pyc()
