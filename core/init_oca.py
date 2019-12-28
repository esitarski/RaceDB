import io
import csv
import sys
import datetime
from six.moves.html_parser import HTMLParser
from html import unescape
from collections import namedtuple
from django.db import transaction
from django.db.models import Q
from .models import *
from .utils import gender_from_str, removeDiacritic

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

fnameDefault = 'GFRR/14_Apr_2015_12_10_22_PM-oca-dougs-report-8fc93c.csv'
fnameDefault = 'GFRR/April 17.csv'

def date_from_str( s ):
	# Assume year, month, day
	yy, mm, dd = [int(v.strip()) for v in s.split( '/' )]
	
	# Correct for day, month, year.
	if dd > 1900:
		dd, mm, yy = yy, mm, dd
	
	# Correct for 2-digit year.
	for century in [0, 1900, 2000, 2100]:
		if earliest_year <= yy + century <= latest_year:
			yy += century
			break
	
	# Check if day and month are reversed.
	if mm > 12:
		dd, mm = mm, dd
		
	assert 1900 <= yy
		
	try:
		return datetime.date( year = yy, month = mm, day = dd )
	except Exception as e:
		print ( yy, mm, dd )
		raise e
		
def set_attributes( obj, attributes ):
	changed = False
	for key, value in attributes.items():
		if getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def init_oca( fname, message_stream=sys.stdout ):
	
	if fname == '_':
		fname = fnameDefault
	
	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( u'{}'.format(s) )
			
	tstart = datetime.datetime.now()
	
	fix_bad_license_codes()
	
	discipline_id = dict( (discipline, Discipline.objects.get(name=discipline)) for discipline in ['Road', 'Track', 'Cyclocross', 'MTB', 'Para'] )
	discipline_cols = {
		'Road':				['national_road', 'provincial_road'],
		'Cyclocross':		['national_cyclocross', 'provincial_cyclocross'],
		'Track':			['track'],
		'MTB':				['cross_country', 'provincial_cross_country', 'downhill', 'fourx'],
		'Para':				['para_cycling'],
	}
	
	effective_date = datetime.date.today()
	
	html_parser = HTMLParser()
	
	# Process the records in larger transactions for performance.
	@transaction.atomic
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_str( ur.dob )
			except Exception as e:
				messsage_stream_write( u'Line {}: Invalid birthdate "{}" ({}) {}\n'.format( i, ur.dob, ur, e ) )
				continue
				
			attributes = {
				'license_code':	ur.license,
				'last_name':	ur.last_name,
				'first_name':	ur.first_name,
				'gender':		gender_from_str(ur.sex),
				'date_of_birth':date_of_birth,
				'state_prov':	'Ontario',
				'nationality':	'Canada',
				'uci_code':		ur.uci_code,
			}
			if attributes['uci_code'][:3] != 'CAN':
				attributes['nationality'] = ''
			try:
				attributes['city'] = ur.city
			except:
				pass
			
			try:
				lh = LicenseHolder.objects.get( license_code=ur.license )
				if set_attributes(lh, attributes):
					lh.save()
			
			except LicenseHolder.DoesNotExist:
				lh = LicenseHolder( **attributes )
				lh.save()
			
			messsage_stream_write( u'{:>6}: {:>8} {:>9} {:>10} {}, {}, ({})\n'.format(
					i, lh.license_code, lh.uci_code, lh.date_of_birth.strftime('%Y/%m/%d'), lh.last_name, lh.first_name, lh.city
				)
			)
			
			team_name = ur.club or ur.trade_team
			TeamHint.objects.filter( license_holder=lh ).delete()
			if team_name:
				team_names = [t.strip() for t in team_name.split(',') if t.strip()]
				for count, team_name in enumerate(team_names):
					team = Team.objects.get_or_create( name=team_name )[0]
					if count == len(team_names)-1:
						for discipline_name, discipline in discipline_id.items():
							for col_name in discipline_cols[discipline_name]:
								if getattr(ur, col_name, None):
									TeamHint( license_holder=lh, team=team, discipline=discipline, effective_date=effective_date ).save()
									break

	ur_records = []
	with io.open(fname, 'r', encoding='utf-8', errors='replace') as fp:
		oca_reader = csv.reader( fp )
		for i, row in enumerate(oca_reader):
			if i == 0:
				# Get the header fields from the first row.
				fields = utils.getHeaderFields( [unescape(v.strip()) for v in row] )
				messsage_stream_write( u'Recognized Header Fields:\n' )
				messsage_stream_write( u'----------------------------\n' )
				messsage_stream_write( u'\n'.join(fields) + u'\n' )
				messsage_stream_write( u'----------------------------\n' )
				
				oca_record = namedtuple('oca_record', fields)
				continue
			
			ur = oca_record( *[unescape(v.strip()) for v in row] )
			
			ur_records.append( (i, ur) )
			if len(ur_records) == 3000:
				process_ur_records( ur_records )
				ur_records = []
			
	process_ur_records( ur_records )
	
	messsage_stream_write( 'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
