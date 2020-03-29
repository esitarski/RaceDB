import os
import sys
import shutil
import zipfile
import tarfile
import subprocess
import argparse
import markdown

from helptxt.version import version

def reset(tarinfo):
	tarinfo.uid = tarinfo.gid = 1000
	tarinfo.uname = "racedb"
	tarinfo.gname = "users"
	return tarinfo

def buildRaceDB(releasedir):
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

	if not os.path.exists(releasedir):
		os.mkdir(releasedir)

	tfname = os.path.join(releasedir, 'RaceDB-Install-{}.tar.xz'.format(version))
	zfname = os.path.join(releasedir, 'RaceDB-Install-{}.zip'.format(version))
	if os.path.exists(tfname):
		os.remove(tfname)
	if os.path.exists(zfname):
		os.remove(zfname)

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
			if f in ('package.py', 'time_zone.py', 'DatabaseConfig.py', 'RaceDB.json', 'AllowedHosts.py', 'FixJsonImport.py'):
				print( '****************************************' )
				print( 'skipping: {}'.format(f) )
				print( '****************************************' )
				continue
			
			fname = os.path.join( root, f )
			if 'racedb' in fname.lower() and fname.lower().endswith('.json'):
				continue
			if any( d in fname for d in ['env', 'EV', 'GFRR', 'usac_heatmap', 'usac_bug', 'test_data', 'migrations_old', "bugs", '.vscode', 'release', 'docker'] ):
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
	

def buildRaceDBContainer(releasedir):
	unixtarname = os.path.join(releasedir, 'RaceDB-Container-Unix-{}.tar.xz'.format(version))
	if os.path.exists(unixtarname):
		os.remove(unixtarname)

	installDir = 'racedb-container'
	dockerDir = 'docker'

	print("Building: {}".format(unixtarname))
	tf = tarfile.open( unixtarname, 'w:xz')
	for fname in ['README.md', 'docker-compose.yml', 'docker-compose-extdb.yml', 'racedb.env', 'racedb.sh', 'bash_aliases']:
		print("Adding {}".format(fname))
		tf.add( os.path.join(dockerDir, fname), os.path.join(installDir, fname), recursive=False, filter=reset )
	print("Adding .dockerdef")
	tf.add( '.dockerdef', os.path.join(installDir, '.dockerdef'), recursive=False, filter=reset )
	tf.close()
	print("Created: {}".format(unixtarname))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Package RaceDB components - DO NOT RUN DIRECTLY. Use compile.sh.')
	parser.add_argument('-r', '--racedb', action='store_true', default=True, help='Package RaceDB')
	parser.add_argument('-c', '--container', action='store_true', default=False, help='Package RaceDB Container')
	parser.add_argument('-a', '--all', action='store_true', default=False, help='Package everything')
	parser.add_argument('-d', '--releasedir', default='release', help='Release Directory (default: release)')

	args = parser.parse_args()
	if args.racedb or args.all:
		buildRaceDB(args.releasedir)

	if args.container or args.all:
		buildRaceDBContainer(args.releasedir)
