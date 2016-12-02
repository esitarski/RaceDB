import re
import sys
import datetime
from collections import namedtuple, defaultdict

from django.db import transaction, IntegrityError
from django.db.models import Q

from xlrd import open_workbook, xldate_as_tuple
import import_utils
from CountryIOC import ioc_from_country
from import_utils import *
from models import *
from FieldMap import standard_field_map, normalize 

def license_holder_import_excel( worksheet_name='', worksheet_contents=None, message_stream=sys.stdout, update_license_codes=False ):
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def message_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def message_stream_write( s ):
			message_stream.write( unicode(s) )
	
	#-------------------------------------------------------------------------------------------------
	discipline_cols = {
		'Road':				['national road', 'provincial road'],
		'Cyclocross':		['national cyclocross', 'provincial cyclocross'],
		'Track':			['track'],
		'MTB':				['cross country', 'provincial cross country', 'downhill', 'fourx'],
		'Para':				['para cycling'],
	}
	discipline_by_name = {}
	for dname in discipline_cols.iterkeys():
		try:
			discipline_by_name[dname] = Discipline.objects.get(name=dname)
		except (Discipline.DoesNotExist,  Discipline.MultipleObjectsReturned):
			pass
	#-------------------------------------------------------------------------------------------------
	
	cpy_prefix = '_CPY_'
	dup_prefix = '_DUP_'
	err_prefix = '_XXX_'
	
	# Clean up all existing cpy or dup codes.
	success = True
	while success:
		success = False
		with transaction.atomic():
			for lh in LicenseHolder.objects.filter( license_code__startswith=cpy_prefix )[:999]:
				lh.license_code = lh.license_code.replace( cpy_prefix, err_prefix )
				lh.save()
				success = True
	success = True
	while success:
		success = False
		with transaction.atomic():
			for lh in LicenseHolder.objects.filter( license_code__startswith=dup_prefix )[:999]:
				lh.license_code = lh.license_code.replace( dup_prefix, err_prefix )
				lh.save()
				success = True
					
	temp_to_existing = {}
	if update_license_codes:
		print 'Replace all the current license codes with unique temp codes...'
		success = True
		while success:
			success = False
			with transaction.atomic():
				for lh in LicenseHolder.objects.all().exclude( license_code__startswith=cpy_prefix )[:999]:
					temp = random_temp_license(cpy_prefix)
					temp_to_existing[temp] = lh.license_code
					lh.license_code = temp
					lh.save()
					success = True
	
	ifm = standard_field_map()
	
	status_count = defaultdict( int )
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			v = ifm.finder( ur )
			
			uci_code = v('uci_code', None)
			uci_id = v('uci_id', None)
			date_of_birth	= v('date_of_birth', None)
			
			# If no date of birth, try to get it from the UCI code.
			if not date_of_birth and uci_code:
				try:
					date_of_birth = datetime.date( int(uci_code[3:7]), int(uci_code[7:9]), int(uci_code[9:11]) )
				except:
					pass
			
			try:
				date_of_birth = date_from_value(date_of_birth)
			except Exception as e:
				message_stream_write( 'Row {}: Ignoring birthdate (must be YYYY-MM-DD) "{}" ({}) {}'.format(
					i, date_of_birth, ur, e)
				)
				date_of_birth = None
			
			# As a last resort, pick the default DOB
			date_of_birth 	= date_of_birth or invalid_date_of_birth
			
			license_code	= to_int_str(v('license_code', u'')).upper().strip()
			last_name		= to_str(v('last_name',u''))
			first_name		= to_str(v('first_name',u''))
			name			= to_str(v('name',u''))
			if not name:
				name = ' '.join( n for n in [first_name, last_name] if n )
			
			gender			= to_str(v('gender',u''))
			gender			= gender_from_str(gender) if gender else None
			
			email			= to_str(v('email', None))
			phone			= to_str(v('phone', None))
			city			= to_str(v('city', None))
			state_prov		= to_str(v('state_prov', None))
			zip_postal		= to_str(v('zip_postal', None))
			nationality		= to_str(v('nationality', None))
			nation_code		= to_str(v('nation_code', None))
			
			bib				= (to_int(v('bib', None)) or None)
			tag				= to_int_str(v('tag', None))
			note		 	= to_str(v('note', None))
			
			emergency_contact_name = to_str(v('emergency_contact_name', None))
			emergency_contact_phone = to_str(v('emergency_contact_phone', None))

			#---------------------------------------------
			
			license_holder_attr_value = {
				'license_code':license_code,
				'last_name':last_name,
				'first_name':first_name,
				'gender':gender,
				'date_of_birth':date_of_birth,
				'uci_code':uci_code,
				'emergency_contact_name':emergency_contact_name,
				'emergency_contact_phone':emergency_contact_phone,
				'email':email,
				'city':city,
				'state_prov':state_prov,
				'nationality':nationality,
				'zip_postal':zip_postal,
				
				'existing_tag':tag,
				'existing_bib':bib,
				'note':note,
			}
			license_holder_attr_value = { a:v for a, v in license_holder_attr_value.iteritems() if v }
			
			#------------------------------------------------------------------------------
			# Get LicenseHolder.
			#
			license_holder = None
			status = 'Unchanged'
			
			#with transaction.atomic():
			if update_license_codes:
				license_holder = LicenseHolder.objects.filter( search_text__startswith=utils.get_search_text([last_name, first_name]) )
				if date_of_birth and date_of_birth != invalid_date_of_birth:
					license_holder = license_holder.filter( date_of_birth=date_of_birth )
				if gender is not None:
					license_holder = license_holder.filter( gender=gender )
				license_holder = license_holder.first()
			else:
				
				if license_code and not license_code.upper() == u'TEMP':
					# Try to find the license holder by license code.
					try:
						license_holder = LicenseHolder.objects.get( license_code=license_code )
					except LicenseHolder.DoesNotExist:
						# No match.  Create a new license holder using the given license code.
						try:
							license_holder = LicenseHolder( **license_holder_attr_value )
							license_holder.save()
							status = 'Added'
						except Exception as e:
							message_stream_write( u'**** Row {}: New License Holder Exception: {}, Name="{}"\n'.format(
									i, e, name,
								)
							)
							continue
				else:
					# No license code.  Try to find the participant by last/first name, [date_of_birth] and [gender].
					q = Q( search_text__startswith=utils.get_search_text([last_name, first_name]) )
					if date_of_birth and date_of_birth != invalid_date_of_birth:
						q &= Q( date_of_birth=date_of_birth )
					if gender is not None:
						q &= Q( gender=gender )
					
					try:
						license_holder = LicenseHolder.objects.get( q )
					except LicenseHolder.DoesNotExist:
						# No name match.
						# Create a temporary license holder.
						try:
							license_holder_attr_value['license_code'] = u'TEMP'
							license_holder = LicenseHolder( **license_holder_attr_value )
							del license_holder_attr_value['license_code']
							license_holder.save()
							status = 'Added'
						
						except Exception as e:
							message_stream_write( u'**** Row {}: New License Holder Exception: {}, Name="{}"\n'.format(
									i, e, name,
								)
							)
							continue
					
					except LicenseHolder.MultipleObjectsReturned:
						message_stream_write( u'**** Row {}: found multiple LicenceHolders matching "Last, First" Name="{}"\n'.format(
								i, name,
							)
						)
						continue
				
				if not license_holder:
					continue
					
				# Update with any new information.
				if update_license_codes and license_holder_attr_value.get('license_code', None) is not None:
					if temp_to_existing.get(license_holder.license_code,None) != license_holder_attr_value['license_code']:
						temp_to_existing[license_holder.license_code] = license_holder_attr_value['license_code']
						status = "LicenseCode Changed"
					del license_holder_attr_value['license_code']
				
				if set_attributes( license_holder, license_holder_attr_value, False ):
					try:
						license_holder.save()
						if status != 'Added':
							status = 'Changed'
					except Exception as e:
						message_stream_write( u'**** Row {}: License Holder Exception: {}, Name="{}"\n'.format(
								i, e, name,
							)
						)
						message_stream.write( u'^^^^ {}\n'.format( u', '.join( u'{}={}'.format(k, v) for k, v in license_holder_attr_value.iteritems()) ) )
						continue
				
				status_count[status] += 1
				if status != 'Unchanged':
					msg = u'Row {:>6}: {}: {:>8} {}\n'.format(
						i,
						status,
						temp_to_existing[license_holder.license_code] if license_holder.license_code in temp_to_existing else license_holder.license_code,
						u', '.join( unicode(v) if v else u'None' for v in [
								license_holder.date_of_birth.strftime('%Y-%m-%d'), license_holder.uci_code,
								u'{} {}'.format(license_holder.first_name, license_holder.last_name),
								license_holder.city, license_holder.state_prov,
								license_holder.emergency_contact_name, license_holder.emergency_contact_phone,
							]
						),
					)
					message_stream_write( msg )
					print removeDiacritic(msg)[:-1]

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
			message_stream_write( u'Reading sheet: {}\n'.format(cur_sheet_name) )
			ws = wb.sheet_by_name(cur_sheet_name)
			break
	
	if not ws:
		message_stream_write( u'Cannot find sheet "{}"\n'.format(sheet_name) )
		return
	
	print 'Process all rows in spreadsheet...'
	num_rows = ws.nrows
	num_cols = ws.ncols
	for r in xrange(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [unicode(f.value).strip() for f in row]
			ifm.set_headers( fields )
			message_stream_write( u'Header Row:\n' )
			for col, f in enumerate(fields, 1):
				name = ifm.get_name_from_alias( f )
				if name is not None:
					message_stream_write( u'        {}. {} --> {}\n'.format(col, f, name) )
				else:
					message_stream_write( u'        {}. ****{} (Ignored)\n'.format(col, f) )
			continue
			
		ur_records.append( (r+1, [v.value for v in row]) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	if update_license_codes:
		print 'Fix all the license codes...'
	
		# Check if the license code changes would cause a conflict.
		# Ignore changes if they do.
		existing = set()
		repairs = set()
		for k, v in temp_to_existing.iteritems():
			if v not in existing:
				existing.add( v )
				continue
			message_stream_write( u'License code "{}" is non-unique.  Changed to "{}"\n'.format(v,k.replace(cpy_prefix, dup_prefix)) )
			repairs.add( k )
		
		for k in repairs:
			temp_to_existing[k] = k.replace(cpy_prefix, dup_prefix)
		
		print "Repairing temporary license codes..."
		bad_licenses = []
		success = True
		while success:
			success = False
			lh, license_code_original, license_code_new = None, None, None
			try:
				with transaction.atomic():
					for lh in LicenseHolder.objects.filter( license_code__startswith=cpy_prefix ).exclude( license_code__in=bad_licenses )[:999]:
						success = True
						license_code_original, license_code_new = lh.license_code, temp_to_existing.get(lh.license_code, lh.license_code)
						license_code_new = re.sub( '_XXX_|_CPY_|_DUP_', 'TEMP_', license_code_new )
						lh.license_code = license_code_new
						lh.license_code = lh.license_code.replace( '_XXX_', 'TEMP_' )
						lh.save()
						
			except Exception as e:
				if license_code_original:
					bad_licenses.append( license_code_original )
				message_stream_write( u'License fix failure: tmp="{}"  new="{}" {} {} {}, {} {}, {} - {} \n'.format(
						license_code_original,
						license_code_new,
						lh.date_of_birth.strftime('%Y-%m-%d'), lh.uci_code,
						lh.last_name, lh.first_name,
						lh.city, lh.state_prov,
						e,
					)
				)
	
	message_stream_write( u'\n' )
	message_stream_write( u'   '.join( u'{}: {}'.format(a, v) for a, v in sorted((status_count.iteritems()), key=lambda x:x[0]) ) )
	message_stream_write( u'\n' )
	message_stream_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
