import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from collections import namedtuple
from models import *
from django.db import transaction
from django.db.models import Q
from utils import toUnicode, removeDiacritic, gender_from_str
import import_utils
from import_utils import *
from django.utils import timezone
from large_delete_all import large_delete_all

def set_attributes( obj, attributes ):
	changed = False
	for key, value in attributes.items():
		if getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def to_int_str( v ):
	try:
		return u'{}'.format(int(v))
	except:
		pass
	return u'{}'.format(v)
		
def to_str( v ):
	return toUnicode(v)

def init_ccn( fname ):
	
	#large_delete_all( LicenseHolder )
	#large_delete_all( Team )
	
	tstart = datetime.datetime.now()
	
	discipline_id = dict( (discipline, Discipline.objects.get(name=discipline)) for discipline in ['Road', 'Track', 'Cyclocross', 'MTB'] )

	effective_date = timezone.localtime(timezone.now()).date()
	
	# Process the records in large transactions for efficiency.
	invalid_date_of_birth = datetime.date(1900, 1, 1)

	@transaction.atomic
	def process_ur_records( ur_records ):
		
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_value( ur.get('DateBirth', '') )
			except Exception as e:
				safe_print( u'Row {}: Invalid birthdate "{}" ({}) {}'.format( i, ur.get('DateBirth',''), ur, e ) )
				continue
				
			if not ur.get('License',''):
				safe_print( u'Row {}: Missing License '.format(i) )
				continue
			
			attributes = {
				'license_code':	to_int_str(ur.get('License','')),
				'last_name':	to_str(ur.get('Name','')).strip(),
				'first_name':	to_str(ur.get('Firstname','')).strip(),
				'gender':		gender_from_str(to_str(ur.get('Sex','m'))),
				'date_of_birth':date_of_birth if date_of_birth and date_of_birth != invalid_date_of_birth else None,
				'uci_code':		to_str(ur.get('Ucicode','')).strip(),
				'city':			to_str(ur.get('City','')).strip(),
				'state_prov':	to_str(ur.get('Province','')).strip(),
				'nationality':  to_str(ur.get('Nat','')).strip(),
			}
			
			if ur.get('Tag','').strip():
				attributes['existing_tag'] = to_int_str(ur.get('Tag','')).strip()
			
			try:
				lh = LicenseHolder.objects.get( license_code=attributes['license_code'] )
				if set_attributes(lh, attributes):
					lh.save()
			
			except LicenseHolder.DoesNotExist:
				lh = LicenseHolder( **attributes )
				lh.save()
			
			fields = {u'i': i}
			fields.update( attributes )
			safe_print(
				u'{i:>6}: {license_code:>8} {date_of_birth:%Y/%m/%d} {uci_code}, {last_name}, {first_name}, {city}, {state_prov}, {nationality}'.format( **fields )
			)
			TeamHint.objects.filter( license_holder=lh ).delete()
			
			team_name = ur.get('Team','')
			if team_name:
				team = Team.objects.get_or_create( name=team_name )[0]
				for id, d in discipline_id.items():
					TeamHint( discipline=d, license_holder=lh, effective_date=effective_date, team=team )
					break
				
	ur_records = []
	wb = open_workbook( fname )
	import_utils.datemode = wb.datemode
	
	ws = None
	for sheet_name in wb.sheet_names():
		safe_print( u'Reading sheet: {}'.format(sheet_name) )
		ws = wb.sheet_by_name(sheet_name)
		break
	
	if not ws:
		safe_print( u'Cannot find sheet.' )
		return
		
	num_rows = ws.nrows
	num_cols = ws.ncols
	for r in range(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [u'{}'.format(f.value).strip() for f in row]
			safe_print( u'\n'.join(fields) )
			continue
			
		ur = dict( (f, row[c].value) for c, f in enumerate(fields) )
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	safe_print( u'Initialization in: ', datetime.datetime.now() - tstart )
