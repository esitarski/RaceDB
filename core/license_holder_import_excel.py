
import sys
import random
import datetime
from collections import namedtuple, defaultdict

from django.db import transaction, IntegrityError
from django.db.models import Q

from xlrd import open_workbook, xldate_as_tuple
import import_utils
from import_utils import *
from models import *

def license_holder_import_excel( worksheet_name='', worksheet_contents=None, message_stream=sys.stdout, update_license_codes=False ):
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( unicode(s) )
	
	# Replace all the current license codes with unique a temp codes.
	cpy_prefix = '_CPY_'
	dup_prefix = '_DUP_'
	temp_to_existing = {}
	if update_license_codes:
		success = True
		while success:
			success = False
			with transaction.atomic():
				for lh in LicenseHolder.objects.all().exclude( license_code__startswith=cpy_prefix )[:999]:
					temp = '{}{}'.format(cpy_prefix,''.join('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[random.randint(0,35)] for i in xrange(32-len(cpy_prefix))))
					temp_to_existing[temp] = lh.license_code
					lh.license_code = temp
					lh.save()
					success = True
	
	license_col_names = ('License','License #','License Numbers','LicenseNumbers','License Code','LicenseCode')
	
	status_count = defaultdict( int )
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			license_code	= to_int_str(get_key(ur, license_col_names, u''))
			last_name		= to_str(get_key(ur,('LastName','Last Name'),u''))
			first_name		= to_str(get_key(ur,('FirstName','First Name'),u''))
			name			= to_str(ur.get('name',u''))
			if not name:
				name = ' '.join( n for n in [first_name, last_name] if n )
			
			gender			= to_str(get_key(ur,('gender','rider gender'),u''))
			gender			= gender_from_str(gender) if gender else None
			
			date_of_birth   = get_key(ur, ('DOB', 'Date of Birth', 'DateofBirth', 'Birthdate'), None)
			if date_of_birth:
				try:
					date_of_birth = date_from_value(date_of_birth)
				except:
					date_of_birth = None
				if date_of_birth == import_utils.invalid_date_of_birth:
					date_of_birth = None
			else:
				date_of_birth = None
			uci_code = to_str(get_key(ur,('UCI Code','UCICode', 'UCI'), None))
			
			email			= to_str(ur.get('email', None))
			city			= to_str(ur.get('city', None))
			state_prov		= to_str(get_key(ur,('stateprov','state','prov','province','state prov'), None))
			nationality		= to_str(get_key(ur,('nationality','nat','nat.'), None))
			
			emergency_contact_name = to_str(get_key(ur,('Emergency Contact','Emergency Contact Name'), None))
			emergency_contact_phone = to_int_str(get_key(ur,('Emergency Phone','Emergency Contact Phone'), None))
			
			zip_postal		= to_str(get_key(ur,('ZipPostal','Zip', 'Postal', 'Zip Code', 'Postal Code', 'ZipCode', 'PostalCode',), None))
			
			license_holder_attr_value = {
				'license_code':license_code,
				'last_name':last_name,
				'first_name':first_name,
				'gender':gender,
				'date_of_birth':date_of_birth,
				'uci_code':uci_code,
				'emergency_contact_name':emergency_contact_name,
				'emergency_contact_phone':emergency_contact_name,
				'email':email,
				'city':city,
				'state_prov':state_prov,
				'nationality':nationality,
				'zip_postal':zip_postal,
			}
			license_holder_attr_value = { a:v for a, v in license_holder_attr_value.iteritems() if v }
			
			#------------------------------------------------------------------------------
			# Get LicenseHolder.
			#
			license_holder = None
			with transaction.atomic():
				status = "Unchanged"
				
				if update_license_codes:
					license_holder = LicenseHolder.objects.filter( last_name__iexact=last_name, first_name__iexact=first_name )
					if date_of_birth:
						license_holder = license_holder.filter( date_of_birth=date_of_birth )
					license_holder = license_holder.first()
				else:
					if not license_code:
						messsage_stream_write( u'**** Row {}: Missing License Code, Name="{}"\n'.format(
							i, name) )
						continue
						
					if license_code.upper().startswith(u'TEMP'):
						messsage_stream_write( u'**** Row {}: Ignoring TEMP LicenseCode: {}, Name="{}"\n'.format(
							i, license_code, name) )
						continue
					
					license_holder = LicenseHolder.objects.filter( license_code=license_code ).first()
					
				if license_holder:
					# Update with any new information.
					if update_license_codes and license_holder_attr_value.get('license_code', None) is not None:
						temp_to_existing[license_holder.license_code] = license_holder_attr_value['license_code']
						del license_holder_attr_value['license_code']
						status = "LicenseCode Changed"
					if set_attributes( license_holder, license_holder_attr_value, False ):
						license_holder.save()
						status = "Changed"
				else:
					try:
						license_holder = LicenseHolder( **license_holder_attr_value )
						license_holder.save()
						status = "Added"
					except Exception as e:
						messsage_stream_write( u'**** Row {}: New License Holder Exception: {}, Name="{}"\n'.format(
								i, e, name,
							)
						)
						continue
				
				status_count[status] += 1
				if status != 'Unchanged':
					messsage_stream_write( u'Row {:>6}: {}: {:>8} {:>10} {}, {}, {}, {}{}\n'.format(
								i,
								status,
								temp_to_existing[license_holder.license_code] if temp_to_existing else license_holder.license_code,
								license_holder.date_of_birth.strftime('%Y-%m-%d'), license_holder.uci_code,
								license_holder.last_name, license_holder.first_name,
								license_holder.city, license_holder.state_prov,
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
		if cur_sheet_name == sheet_name or sheet_name is None:
			messsage_stream_write( u'Reading sheet: {}\n'.format(cur_sheet_name) )
			ws = wb.sheet_by_name(cur_sheet_name)
			break
	
	if not ws:
		messsage_stream_write( u'Cannot find sheet "{}"\n'.format(sheet_name) )
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
				messsage_stream_write( u'            {}\n'.format(f) )
			
			fields_lower = [f.lower() for f in fields]
			if not any( r.lower() in fields_lower for r in license_col_names ):
				messsage_stream_write( u'License column not found in Header Row.  Aborting.\n' )
				return
			continue
			
		ur = { f.strip().lower(): row[c].value for c, f in enumerate(fields) }
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 999:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	# Fix all the license codes.
	if update_license_codes:
	
		# Check if the license code changes would cause a conflict.
		# Ignore changes if they do.
		existing = set()
		repairs = set()
		for k, v in temp_to_existing.iteritems():
			if v not in existing:
				existing.add( v )
				continue
			messsage_stream_write( u'License code "{}" is non-unique.  Changed to "{}"\n'.format(v,k.replace(cpy_prefix, dup_prefix)) )
			repairs.add( k )
		
		for k in repairs:
			temp_to_existing[k] = k.replace(cpy_prefix, dup_prefix)
		
		success = True
		while success:
			success = False
			with transaction.atomic():
				for lh in LicenseHolder.objects.filter( license_code__startswith=cpy_prefix )[:999]:
					lh.license_code = temp_to_existing[lh.license_code]
					lh.save()
					success = True
	
	messsage_stream_write( u'\n' )
	messsage_stream_write( u'   '.join( u'{}: {}'.format(a, v) for a, v in sorted((status_count.iteritems()), key=lambda x:x[0]) ) )
	messsage_stream_write( u'\n' )
	messsage_stream_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
