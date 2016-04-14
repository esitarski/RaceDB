import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from django.db import transaction, IntegrityError
from django.db.models import Q
from large_delete_all import large_delete_all
import import_utils
from import_utils import *
from models import *

def init_seasons_pass( seasonsPassId, worksheet_name='', worksheet_contents=None, message_stream=sys.stdout, clear_existing=False ):
	
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( unicode(s) )
	
	try:
		seasons_pass = SeasonsPass.objects.get( pk=seasonsPassId )
	except SeasonsPass.DoesNotExist:
		messsage_stream_write( u'**** Cannot find SeasonsPass\n' )
		return
		
	if clear_existing:
		large_delete_all( SeasonsPassHolder, Q(seasons_pass=seasons_pass) )
	
	license_col_names = ('License','License #','License Numbers','LicenseNumbers','License Code','LicenseCode')
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			
			license_code = to_int_str(get_key(ur, license_col_names, u'')).upper().strip()
			last_name		= to_str(get_key(ur,('LastName','Last Name'),u''))
			first_name		= to_str(get_key(ur,('FirstName','First Name'),u''))
			date_of_birth	= get_key(ur, ('Date of Birth', 'Birthdate', 'DOB'), None)
			try:
				date_of_birth = date_from_value(date_of_birth)
			except Exception as e:
				messsage_stream_write( 'Row {:>6}: Invalid birthdate (ignoring) "{}" ({}) {}'.format( i, date_of_birth, ur, e ) )
				date_of_birth = None
			date_of_birth 	= date_of_birth if date_of_birth != import_utils.invalid_date_of_birth else None

			license_holder = None
			if license_code:
				try:
					license_holder = LicenseHolder.objects.get( license_code=license_code )
				except LicenseHolder.DoesNotExist:
					messsage_stream_write( u'**** Row {}: cannot find LicenceHolder from LicenseCode: "{}"\n'.format(
						i, license_code) )
					continue
				
			elif last_name:
				q = Q(search_text__startswith=utils.get_search_text([last_name,first_name]))
				if date_of_birth:
					q &= Q(date_of_birth=date_of_birth)
				try:
					license_holder = LicenseHolder.objects.get( q )
				except LicenseHolder.DoesNotExist:
					messsage_stream_write( u'**** Row {}: cannot find LicenceHolder: "{}, {}" {}\n'.format(
						i, last_name, first_name, date_of_birth if date_of_birth else '')
					)
					continue
				except LicenseHolder.MultipleObjectsReturned:
					messsage_stream_write( u'**** Row {}: found multiple LicenceHolders matching "{}, {}" {}\n'.format(
						i, last_name, first_name, date_of_birth if date_of_birth else '')
					)
					continue

			else:
				messsage_stream_write(
					u'Row {i:>6}: Missing License or LastName, FirstName [Date of Birth]\n'.format(
						i=i,
					)
				)
				continue
				
			if not license_holder:
				continue
			
			seasons_pass.add( license_holder )
			messsage_stream_write(
				u'Row {i:>6}: {license_code:>8} {dob:>10} {uci_code}, {last_name}, {first_name}, {city}, {state_prov}\n'.format(
					i=i,
					license_code=license_holder.license_code,
					dob=license_holder.date_of_birth.strftime('%Y-%m-%d'),
					uci_code=license_holder.uci_code,
					last_name=license_holder.last_name,
					first_name=license_holder.first_name,
					city=license_holder.city, state_prov=license_holder.state_prov,
				)
			)
			
	
	sheet_name = None
	if worksheet_contents is not None:
		wb = open_workbook( file_contents = worksheet_contents )
	else:
		try:
			fname, sheet_name = worksheet_name.split('$')
		except:
			fname = worksheet_name
		wb = open_workbook( fname )
	
	ur_records = []
	import_utils.datemode = wb.datemode
	
	ws = None
	for cur_sheet_name in wb.sheet_names():
		messsage_stream_write( u'Reading sheet: {}\n'.format(cur_sheet_name) )
		ws = wb.sheet_by_name(cur_sheet_name)
		break
	
	if not ws:
		messsage_stream_write( u'Cannot find sheet.\n' )
		return
		
	num_rows = ws.nrows
	num_cols = ws.ncols
	for r in xrange(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [unicode(f.value).strip() for f in row]
			messsage_stream_write( u'Header Row:\n' )
			for f in fields:
				messsage_stream_write( u'   {}\n'.format(f) )
			
			fields_lower = [f.lower() for f in fields]
			if not any( r.lower() in fields_lower for r in license_col_names ):
				messsage_stream_write( u'License column not found in Header Row.  Aborting.\n' )
				return
			continue
			
		ur = { f.strip().lower(): row[c].value for c, f in enumerate(fields) }
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	messsage_stream_write( u'\n' )
	messsage_stream_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
