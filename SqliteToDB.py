import os
import re
import sys
import json
import shutil
import argparse
import datetime
import sqlite3
import operator
from subprocess import call, run, check_call, PIPE
from collections import defaultdict

import warnings
warnings.filterwarnings("ignore")

# Import a RaceDB.sqlite3 database into a configured database.

Sqlite3FName = 'RaceDB.sqlite3'
# Check alternative RaceDB.sqlite3 locations.
if os.path.isfile(os.path.join( 'racedb-data',  Sqlite3FName )):
	Sqlite3FName = os.path.join( 'racedb-data',  Sqlite3FName )

parser = argparse.ArgumentParser(description='Import an sqlite3 database file into the current database.')
parser.add_argument('Sqlite3FName', nargs='?', default=Sqlite3FName)
args = parser.parse_args()

Sqlite3FName = args.Sqlite3FName

if not os.path.isfile(Sqlite3FName):
	print( '**** Missing RaceDB.sqlite3 file.  Aborting.' )
	sys.exit( -1 )

JSONFName = os.path.splitext(Sqlite3FName)[0] + '.json'

class Sqlite3ToJson:
	'''
		Convert a Django sqlite3 file to a Django-compatable json without Django models.py or setting.py.
		Objects are streamed one at a time to minimize memory use.
	'''
	def __init__( self, sqlite_fname, json_fname, app_name ):
		self.sqlite_fname = sqlite_fname
		self.json_fname = json_fname
		self.app_name = app_name
		
	def table_to_json( self, table, table_name ):
		cursor = self.conn.cursor()
		for row in cursor.execute('SELECT * from {};'.format(table) ):
			# Transform record to Django's object format.
			r = {cursor.description[i][0]:value for i, value in enumerate(row)}
			d = {'model':table_name, 'pk':r['id']}
			del r['id']
			d['fields'] = r
			if self.count != 0:
				self.json_f.write( ',\n' )
			json.dump( d, self.json_f, indent=1 )
			self.count += 1
			
	def to_json( self ):
		self.conn = sqlite3.connect( self.sqlite_fname )	
		cursor = self.conn.cursor()

		self.count = 0
		with open(self.json_fname, 'w') as self.json_f:
			self.json_f.write( '[\n' )
			for t in cursor.execute('SELECT name from sqlite_master where type="table";'):
				table = t[0]
				if table.startswith(self.app_name):
					# Get table name in Django convention.
					self.table_to_json( table, table[:len(self.app_name)-1] + '.' + table[len(self.app_name):] )
			self.json_f.write( ']\n' )
			
		return self.count

reNoSpace = re.compile('\u200B', flags=re.UNICODE)
reAllSpace = re.compile(r'\s', flags=re.UNICODE)
def fix_spaces( v ):
	if v and isinstance(v, str):
		v = reNoSpace.sub( '', v )		# Replace zero space with nothing.
		v = reAllSpace.sub( ' ', v )	# Replace alternate spaces with a regular space.
		v = v.strip()
	return v

def json_cleanse( fname ):
	with open(fname, 'r') as pf:
		rows = json.load( pf )
		
	for r in rows:
		fields = r.get('fields',{})
		for attr in ('tag', 'tag2'):
			tag = fields.get(attr,None)
			if tag:
				fields[attr] = tag[:36]
		
		for f in list(fields.keys()):
			v = fields[f]
			if isinstance(v, str):
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
		self.sequence = {}
		
	def start( self, label ):
		if label:
			print( '****', label, '...' )
		t = datetime.datetime.now()
		if self.curLabel and self.startTime:
			self.totals[self.curLabel] += (t - self.startTime).total_seconds()
		self.curLabel = label
		self.startTime = t
		if label not in self.sequence:
			self.sequence[label] = len(self.sequence)
		
	def end( self ):
		self.start( None )
		
	def __repr__( self ):
		s = []
		tTotal = 0.0
		for lab, t in sorted( self.totals.items(), key=lambda x: self.sequence.get(x[0], 999) ):
			s.append( '{:<50}: {:>12}'.format(lab, format_time(t)) )
			tTotal += t
		s.append( '-' * 64 )
		s.append( '{:<50}: {:>12}'.format('Total', format_time(tTotal)) )
		s.append( '' )
		return '\n'.join( s )

def filter_errors( output, stream ):
	for line in output.split('\n'):
		if 'received a naive datetime' not in line:
			print( line, file=stream )

def handle_call( args ):
	#check_call( args )
	ret = run( args, capture_output=True, universal_newlines=True )
	filter_errors( ret.stdout, sys.stdout )
	filter_errors( ret.stderr, sys.stderr )
	ret.check_returncode()					# Throws exception on non-zero return.
	
python = (sys.executable or python)
	
tt = TimeTracker()

tt.start('migrating existing database')
handle_call( [python, 'manage.py', 'migrate'] )

from contextlib import redirect_stdout, redirect_stderr
class message_filter:
	def __init__( self, output ):
		self.output = output
		
	def write( self, data ):
		if not 'received a naive datetime' in data:
			print( data, file=self.output)
		
tt.start('extracting json data from sqlite3 database' )
with redirect_stdout( message_filter(sys.stdout) ):
	with redirect_stderr( message_filter(sys.stderr) ):
		Sqlite3ToJson( Sqlite3FName, JSONFName, 'core_' ).to_json()

tt.start( 'cleansing json data' )
json_cleanse( JSONFName )

tt.start('dropping existing data')
handle_call( [python, 'manage.py', 'flush', '--noinput'] )

tt.start( 'creating standard users' )
handle_call( [python, 'manage.py', 'create_users'] )
	
try:
	tt.start('loading json data from sqlite3 database')
	handle_call( [python, 'manage.py', 'loaddata', JSONFName] )
finally:
	os.remove( JSONFName )

tt.start( 'fixing imported data' )
handle_call( [python, 'manage.py', 'fix_data'] )
	
tt.end()
sys.stderr.write( '\n' )
sys.stderr.write( repr(tt) )
