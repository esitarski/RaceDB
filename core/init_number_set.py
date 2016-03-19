import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from django.db import transaction, IntegrityError
from django.db.models import Q
import import_utils
from import_utils import *
from models import *

def init_number_set( numberSetId, worksheet_name='', worksheet_contents=None, message_stream=sys.stdout ):
	
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( unicode(s) )
	
	try:
		number_set = NumberSet.objects.get( pk=numberSetId )
	except NumberSet.DoesNotExist:
		messsage_stream_write( u'**** Cannot find NumberSet\n' )
		return
	
	license_col_names = ('License','License #','License Numbers','LicenseNumbers','License Code','LicenseCode')
	bib_col_names = ('bib', 'bib#', 'bib #')
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			bib = get_key(ur, bib_col_names, u'')
			if not bib:
				continue
			try:
				bib = int(bib)
			except ValueError:
				messsage_stream_write( u'**** Row {}: invalid Bib: {}"\n'.format(
					i, bib) )
				continue
			
			license_code = to_int_str(get_key(ur, license_col_names, u'')).upper().strip()
			if license_code:
				try:
					license_holder = LicenseHolder.objects.get( license_code=license_code )
				except LicenseHolder.DoesNotExist:
					messsage_stream_write( u'**** Row {}: cannot find LicenceHolder from LicenseCode: "{}"\n'.format(
						i, license_code) )
					continue
				
				number_set.assign_bib( license_holder, bib )
				messsage_stream_write(
					u'Row {i:>6}: {bib:>4} {license_code:>8} {dob:>10} {uci_code}, {last_name}, {first_name}, {city}, {state_prov}\n'.format(
						i=i,
						bib=bib,
						license_code=license_holder.license_code,
						dob=license_holder.date_of_birth.strftime('%Y-%m-%d'),
						uci_code=license_holder.uci_code,
						last_name=license_holder.last_name,
						first_name=license_holder.first_name,
						city=license_holder.city, state_prov=license_holder.state_prov,
					)
				)
			else:
				number_set.set_lost( bib )
				messsage_stream_write(
					u'Row {i:>6}: {bib:>4} Lost\n'.format(
						i=i,
						bib=bib,
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
			if not any( r.lower() in fields_lower for r in bib_col_names ):
				messsage_stream_write( u'Bib column not found in Header Row.  Aborting.\n' )
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
