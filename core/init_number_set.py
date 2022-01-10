import sys
import datetime
from openpyxl import load_workbook
from io import BytesIO
from django.db import transaction, IntegrityError
from django.db.models import Q
from . import import_utils
from .import_utils import *
from .models import *

def init_number_set( numberSetId, worksheet_name='', worksheet_contents=None, message_stream=sys.stdout ):
	
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( '{}'.format(s) )
	
	try:
		number_set = NumberSet.objects.get( pk=numberSetId )
	except NumberSet.DoesNotExist:
		messsage_stream_write( '**** Cannot find NumberSet\n' )
		return
	
	license_col_names = ('License','License #','License Numbers','LicenseNumbers','License Code','LicenseCode')
	bib_col_names = ('bib', 'bib#', 'bib #')
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			bib = get_key(ur, bib_col_names, '')
			if not bib:
				continue
			try:
				bib = int(bib)
			except ValueError:
				messsage_stream_write( '**** Row {}: invalid Bib: {}"\n'.format(
					i, bib) )
				continue
			
			license_code = to_int_str(get_key(ur, license_col_names, '')).upper().strip()
			if license_code:
				try:
					license_holder = LicenseHolder.objects.get( license_code=license_code )
				except LicenseHolder.DoesNotExist:
					messsage_stream_write( '**** Row {}: cannot find LicenceHolder from LicenseCode: "{}"\n'.format(
						i, license_code) )
					continue
				
				if not number_set.assign_bib( license_holder, bib ):
					messsage_stream_write( '**** Row {}: bib={} cannot be assigned.  The bib must be valid and allowed by the NumberSet ranges?\n'.format(
						i, bib) )
					
				messsage_stream_write(
					'Row {i:>6}: {bib:>4} {license_code:>8} {dob:>10} {uci_id}, {last_name}, {first_name}, {city}, {state_prov}\n'.format(
						i=i,
						bib=bib,
						license_code=license_holder.license_code,
						dob=license_holder.date_of_birth.strftime('%Y-%m-%d'),
						uci_id=license_holder.uci_id,
						last_name=license_holder.last_name,
						first_name=license_holder.first_name,
						city=license_holder.city, state_prov=license_holder.state_prov,
					)
				)
			else:
				number_set.set_lost( bib )
				messsage_stream_write(
					'Row {i:>6}: {bib:>4} Lost\n'.format(
						i=i,
						bib=bib,
					)
				)
			
	
	sheet_name = None
	if worksheet_contents is not None:
		wb = load_workbook( filename = BytesIO(worksheet_contents), read_only=True, data_only=True )
	else:
		try:
			fname, sheet_name = worksheet_name.split('$')
		except Exception:
			fname = worksheet_name
		wb = load_workbook( filename = fname, read_only=True, data_only=True )
	
	try:
		sheet_name = sheet_name or wb.sheetnames[0]
		ws = wb[sheet_name]
		message_stream_write( 'Reading sheet "{}"\n'.format(sheet_name) )
	except Exception as e:
		message_stream_write( 'Cannot find sheet "{} ({})"\n'.format(sheet_name, e) )
		return
		
	ur_records = []
	for r, row in enumerate(ws.iter_rows()):
		if r == 0:
			# Get the header fields from the first row.
			fields = {col:'{}'.format(f.value).strip() for col, f in enumerate(row)}
			messsage_stream_write( 'Header Row:\n' )
			for f in fields.values():
				messsage_stream_write( '   {}\n'.format(f) )
			
			fields_lower = set( f.lower() for f in fields.keys() )
			if not any( n.lower() in fields_lower for n in license_col_names ):
				messsage_stream_write( 'License column not found in Header Row.  Aborting.\n' )
				return
			if not any( n.lower() in fields_lower for n in bib_col_names ):
				messsage_stream_write( 'Bib column not found in Header Row.  Aborting.\n' )
				return
			continue
			
		ur = { fields.get(col,'').lower():cell.value for col, cell in enumerate(row) }
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	messsage_stream_write( '\n' )
	messsage_stream_write( 'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
