import os
import re
import sys
import six
import json
import fnmatch
import shutil
import datetime
from collections import defaultdict
import operator
from subprocess import call, check_call

# Import a RaceDB.sqlite3 database into a configured database.
# You must configure the database connection in DatabaseConfig.py.

RaceDBDir = 'RaceDB'
DatabaseConfigFName = os.path.join(RaceDBDir, 'DatabaseConfig.py')
DatabaseConfigFNameSave = os.path.splitext(DatabaseConfigFName)[0] + '.py.Save'
JsonFName = 'RaceDB.json'
Sqlite3FName = 'RaceDB.sqlite3'

reNoSpace = re.compile(u'\u200B', flags=re.UNICODE)
reAllSpace = re.compile(r'\s', flags=re.UNICODE)
def fix_spaces( v ):
	if v and isinstance(v, six.string_types):
		v = reNoSpace.sub( u'', v )		# Replace zero space with nothing.
		v = reAllSpace.sub( u' ', v )	# Replace alternate spaces with a regular space.
		v = v.strip()
	return v

def json_cleanse( fname ):
	with open(fname, 'r') as pf:
		rows = json.load( pf )
		
	for r in rows:
		fields = r.get('fields',{})
		for f in list(fields.iterkeys()):
			v = fields[f]
			if isinstance(v, six.string_types):
				fields[f] = fix_spaces( v )
				
	with open(fname, 'w') as pf:
		json.dump( rows, pf )

def format_time( secs ):
	t = '{:.2f}'.format( secs )
	decimals = t[-3:]
	n = int(t[:-3])
	hh = n//(60*60)
	mm = (n//60)%60
	ss = n%60
	return '{}:{:02d}:{:02d}{}'.format(hh,mm,ss,decimals)
	
class TimeTracker( object ):
	def __init__( self ):
		self.startTime = None
		self.curLabel = None
		self.totals = defaultdict( float )
		
	def start( self, label ):
		t = datetime.datetime.now()
		if self.curLabel and self.startTime:
			self.totals[self.curLabel] += (t - self.startTime).total_seconds()
		self.curLabel = label
		self.startTime = t
		
	def end( self ):
		self.start( None )
		
	def __repr__( self ):
		s = []
		tTotal = 0.0
		for lab, t in sorted( self.totals.items(), key=operator.itemgetter(1), reverse=True ):
			s.append( '{:<50}: {:>12}'.format(lab, format_time(t)) )
			tTotal += t
		s.append( '-' * 64 )
		s.append( '{:<50}: {:>12}'.format('Total', format_time(tTotal)) )
		s.append( '' )
		return '\n'.join( s )

def find_files(directory, pattern):
	for root, dirs, files in os.walk(directory):
		for basename in files:
			if fnmatch.fnmatch(basename, pattern):
				yield os.path.join(root, basename)

def switch_configuration( to_database ):
	if to_database:
		sys.stderr.write( '**** Switching to Database configuration...\n' )
		f_from, f_to = DatabaseConfigFNameSave, DatabaseConfigFName
	else:
		sys.stderr.write( '**** Switching to Sqlite3 configuration...\n' )
		f_to, f_from = DatabaseConfigFNameSave, DatabaseConfigFName
	try:
		shutil.move( f_from, f_to )
	except:
		sys.stderr.write( '**** Failure: Cannot rename {} to {}.\n'.format(f_from, f_to) )
		sys.exit()
	# Make sure to remove the .pyc files so python won't use them instead.
	for pyc in find_files(RaceDBDir, '*.pyc'):
		os.remove( pyc )

# Cache a copy of the configuration file.
with open(DatabaseConfigFName, 'r') as fp:
	database_config = fp.read()
	
def handle_call( args ):
	try:
		check_call( args )
	except:
		# Restore the configuration file if anything goes wrong.
		with open(DatabaseConfigFName, 'w') as fp:
			fp.write( database_config )
		raise

tt = TimeTracker()
		
tt.start('migrating database')
sys.stderr.write( '**** Migrating DB...\n' )
handle_call( ['python', 'manage.py', 'migrate'] )

switch_configuration( to_database=False )

tt.start('migrating sqlite3 database')
sys.stderr.write( '**** Migrating RaceDB.sqlite3...\n' )
handle_call( ['python', 'manage.py', 'migrate'] )

tt.start('fixing sqlite3 database')
sys.stderr.write( '**** Fixing RaceDB.sqlite3 data...\n' )
handle_call( ['python', 'manage.py', 'fix_data'] )

tt.start('extracting json data from sqlite3')
sys.stderr.write( '**** Extracting RaceDB.sqlite3 data to {}...\n'.format(JsonFName) )
handle_call( ['python', 'manage.py', 'dumpdata', 'core', '--output', JsonFName] )

tt.start( 'cleansing json data' )
sys.stderr.write( '**** Cleansing Json File...\n' )
json_cleanse( JsonFName )

switch_configuration( to_database=True )
tt.start('dropping existing data')
sys.stderr.write( '**** Dropping existing database data...\n' )
handle_call( ['python', 'manage.py', 'flush', '--noinput'] )

try:
	sys.stderr.write( '**** Loading data into database...\n' )
	tt.start('loading data')
	handle_call( ['python', 'manage.py', 'loaddata', JsonFName] )
finally:
	sys.stderr.write( 'Cleanup...\n' )
	os.remove( JsonFName )

tt.start( 'creating standard users' )
handle_call( ['python', 'manage.py', 'create_users'] )
	
tt.end()
sys.stderr.write( '\n' )
sys.stderr.write( repr(tt) )
