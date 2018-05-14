import os
import sys
import fnmatch
import shutil
import datetime
from collections import defaultdict
import operator
from subprocess import check_call

# Extract a MySql, Postgres or Oracle database and create an sqlite database file.
# You must configure the database connection in DatabaseConfig.py.

RaceDBDir = 'RaceDB'
DatabaseConfigFName = os.path.join(RaceDBDir, 'DatabaseConfig.py')
DatabaseConfigFNameSave = os.path.splitext(DatabaseConfigFName)[0] + '.py.Save'
JsonFName = 'RaceDB.json'
Sqlite3FName = 'RaceDB.sqlite3'

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
		for lab, t in sorted( self.totals.iteritems(), key=operator.itemgetter(1), reverse=True ):
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
		sys.stderr.write( 'Switching to Database configuration...\n' )
		f_from, f_to = DatabaseConfigFNameSave, DatabaseConfigFName
	else:
		sys.stderr.write( 'Switching to Sqlite3 configuration...\n' )
		f_to, f_from = DatabaseConfigFNameSave, DatabaseConfigFName
	try:
		shutil.move( f_from, f_to )
	except:
		sys.stderr.write( 'Failure: Cannot rename {} to {}.\n'.format(f_from, f_to) )
		sys.exit()
	# Make sure to remove the .pyc files so python won't use them instead.
	for pyc in find_files(RaceDBDir, '*.pyc'):
		os.remove( pyc )

# Cache a copy of the configuration file.
with open(DatabaseConfigFName, 'r') as fp:
	database_config = fp.read()
	
def hande_call( args ):
	try:
		check_call( args )
	except:
		# Restore the configuration file if anything goes wrong.
		with open(DatabaseConfigFName, 'w') as fp:
			fp.write( database_config )
		raise
		
tt = TimeTracker()

tt.start( 'extracting json data' )
sys.stderr.write( '**** Extracting database data to {}...\n'.format(JsonFName) )
handle_call( ['python', 'manage.py', 'dumpdata', 'core', '--output', JsonFName] )

sys.stderr.write( '**** Initializing {}...\n'.format(Sqlite3FName) )
tt.start( 'initializing sqlite3 database' )
switch_configuration( to_database=False )
# Delete and re-create the sqlite3 file as it is the fastest way to initialize it.
try:
	os.remove( Sqlite3FName )
except:
	pass	# May fail if file doesn't exist.  That's OK.
handle_call( ['python', 'manage.py', 'migrate'] )

tt.start( 'loading json data' )
handle_call( ['python', 'manage.py', 'loaddata', JsonFName] )

tt.start( 'creating standard users' )
handle_call( ['python', 'manage.py', 'create_users'] )
	
switch_configuration( to_database=True )

tt.end()
sys.stderr.write( '**** Cleanup...\n' )
os.remove( JsonFName )
sys.stderr.write( repr(tt) )