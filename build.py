import os
import shutil
import zipfile
import subprocess

from helptxt.compile import CompileHelp
from helptxt.version import version
from manage import managemain

# Delete any existing releases that are unofficial.
officialReleases = ['1.32.116',]
	
def build():
	CompileHelp( 'helptxt' )
	managemain( ['manage.py', 'collectstatic', '--noinput'] )

	installDir = 'RaceDB'

	zfname = os.path.join('install', 'RaceDB-Install-{}.zip'.format(version))
	zf = zipfile.ZipFile( zfname, 'w' )

	# Write all important source files to the install zip.
	suffixes = {
		'py',
		'txt', 'md',
		'html', 'css', 'js',
		'png', 'gif', 'jpg', 'ico',
		'json',
		'xls', 'xlsx',
		'gz',
		'ttf',
		'bash',
	}
	for root, dirs, files in os.walk('.'):
		for f in files:
		
			# Don't include local configuration in the install.
			if f in ('time_zone.py', 'DatabaseConfig.py', 'RaceDB.json', 'AllowedHosts.py', 'FixJsonImport.py'):
				print( '****************************************' )
				print( 'skipping: {}'.format(f) )
				print( '****************************************' )
				continue
			
			fname = os.path.join( root, f )
			if 'racedb' in fname.lower() and fname.lower().endswith('.json'):
				continue
			if any( d in fname for d in ['EV', 'GFRR', 'usac_heatmap', 'usac_bug', 'test_data', 'migrations_old', "bugs"] ):
				continue
			if os.path.splitext(fname)[1][1:] in suffixes:
				print( 'writing: {}'.format(fname) )
				zf.write( fname, os.path.join(installDir, fname) )

    # pyllrp  is not downloaded from git, so we no longer include it here
	zf.close()
	

if __name__ == '__main__':
	build()
