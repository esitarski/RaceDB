import os
import sys
import shutil
import zipfile
import tarfile
import subprocess

from helptxt.version import version

def reset(tarinfo):
	tarinfo.uid = tarinfo.gid = 1000
	tarinfo.uname = "racedb"
	tarinfo.gname = "users"
	return tarinfo

def build():
	try:
		virtenv = os.environ['VIRTUAL_ENV']
	except:
		print("Refusing to build outside the virtual env")
		sys.exit(1)
	print("Building version: {}".format(version))
	from helptxt.compile import CompileHelp
	CompileHelp( 'helptxt' )
	subprocess.call( ['python3', 'manage.py', 'collectstatic', '--noinput'] )

	installDir = 'RaceDB'

	if not os.path.exists('release'):
		os.mkdir('release')

	tfname = os.path.join('release', 'RaceDB-Install-{}.tar.xz'.format(version))
	zfname = os.path.join('release', 'RaceDB-Install-{}.zip'.format(version))
	tf = tarfile.open( tfname, 'w:xz')
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
			if f in ('build.py', 'time_zone.py', 'DatabaseConfig.py', 'RaceDB.json', 'AllowedHosts.py', 'FixJsonImport.py'):
				print( '****************************************' )
				print( 'skipping: {}'.format(f) )
				print( '****************************************' )
				continue
			
			fname = os.path.join( root, f )
			if 'racedb' in fname.lower() and fname.lower().endswith('.json'):
				continue
			if any( d in fname for d in ['env', 'EV', 'GFRR', 'usac_heatmap', 'usac_bug', 'test_data', 'migrations_old', "bugs"] ):
				continue
			if os.path.splitext(fname)[1][1:] in suffixes:
				print( 'writing: {}'.format(fname[2:]))
				zf.write( fname, os.path.join(installDir, fname) )
				# Strip off the ./
				tf.add( fname, os.path.join(installDir, fname[2:]), recursive=False, filter=reset )

	zf.close()
	tf.close()
	print("Created: {}".format(zfname))
	print("Created: {}".format(tfname))
	

if __name__ == '__main__':
	build()
