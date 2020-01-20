import os
import sys
import shutil
import zipfile
import subprocess

from helptxt.compile import CompileHelp

def updateversion():
	retversion=''
	try:
		githubref = os.environ['GITHUB_REF']
	except:
		githubref=''
	if githubref:
		from helptxt.version import version
		newversion=''
		(ref, reftype, tag) = githubref.split('/')
		(version, date) = version.split('-')
		fullsha = os.environ['GITHUB_SHA']
		shortsha=fullsha[0:7]
		print("type: {} tag: {}".format(reftype, tag))
		print("version: {} shortsha: {}".format(version, shortsha))
		if reftype == "heads" and tag == "master":
			print("Refusing to build an untagged master build. Release builds on a tag only!")
			sys.exit(1)
		if reftype == 'heads' and tag == 'dev':
			newversion="version=\"{}-beta-{}\"\n".format(version, shortsha)
			retversion="{}-beta-{}".format(version, shortsha)
		if reftype == 'tags':
			(version, refdate) = tag.split('-')
			(major, minor, release) = version.split('.')
			if major != "v3" or not minor or not release or not refdate:
				print("Invalid tag format. Must be v3.0.3-20200101010101. Refusing to build!")
				sys.exit(1)
			newversion = "version=\"v3.{}.{}-{}\"\n".format(minor, release, refdate)
			retversion = "v3.{}.{}-{}".format(minor, release, refdate)
		if not newversion:
			print("newversion is empty! Refusing to build!")
			sys.exit(1)
		print("New version: {}".format(newversion))
		f = open("helptxt/version.py", 'w')
		f.write(newversion)
		f.close()
	else:
		from helptxt.version import version
		print("Creating local build: {}".format(version))
		retversion=version
	return retversion

def build(version):
	print("Building version: {}".format(version))
	CompileHelp( 'helptxt' )
	subprocess.call( ['python3', 'manage.py', 'collectstatic', '--noinput'] )

	installDir = 'RaceDB'

	if not os.path.exists('release'):
		os.mkdir('release')

	zfname = os.path.join('release', 'RaceDB-Install-{}.zip'.format(version))
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
			if any( d in fname for d in ['env', 'EV', 'GFRR', 'usac_heatmap', 'usac_bug', 'test_data', 'migrations_old', "bugs"] ):
				continue
			if os.path.splitext(fname)[1][1:] in suffixes:
				print( 'writing: {}'.format(fname) )
				zf.write( fname, os.path.join(installDir, fname) )

    # pyllrp  is not downloaded from git, so we no longer include it here
	zf.close()
	print("Created: {}".format(zfname))
	

if __name__ == '__main__':
	version = updateversion()
	build(version)
