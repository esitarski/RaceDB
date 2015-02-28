#!/usr/bin/env python
from utils import toUnicode, removeDiacritic
import sqlite3
import sys

# Normalize imported database text fields to utf8.

dbFileNameDefault = 'RaceDB.sqlite3'

license_holder_fields = [
	'search_text',
	'last_name', 'first_name',
	'license_code', 'uci_code',
	'nationality', 'state_prov', 'city',
	'existing_tag', 'existing_tag2',
]

team_fields = [
	'name',
	'team_code',
	'nation_code',
	'search_text',
]

table_fields = [
	('core_licenseholder', license_holder_fields),
	('core_team', team_fields),
]

def fix_utf8( dbFileName = dbFileNameDefault ):
	try:
		db = sqlite3.connect( dbFileName )
	except Exception as e:
		print e
		sys.exit()
		
	db.text_factory = toUnicode
	cursor = db.cursor()
	
	for table, fields in table_fields:
		print 'Scanning:', table
		cursor.execute( 'SELECT {}, id FROM {}'.format( ', '.join(fields), table ) )
		info = [[field.encode('utf-8') if field is not None else None for field in row[:-1]] + [row[-1]] for row in cursor.fetchall()]
		cursor.executemany( 'UPDATE {} SET {} where id=?'.format( table, ', '.join('{}=?'.format(field_name) for field_name in fields)), info )
		db.commit()
	
	db.close()
	
if __name__ == '__main__':
	fix_utf8()