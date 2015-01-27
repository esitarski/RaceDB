import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from collections import namedtuple
from models import *
from utils import toUnicode, removeDiacritic
from django.db import transaction
from django.db.models import Q

datemode = None

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

def date_from_value( s ):
	if isinstance(s, datetime.date):
		return s
	if isinstance(s, (float, int)):
		return datetime.date( *(xldate_as_tuple(s, datemode)[:3]) )
	
	# Assume month, day, year format.
	mm, dd, yy = [int(v.strip()) for v in s.split( '/' )]
	
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
		print yy, mm, dd
		raise e
		
def gender_from_str( s ):
	return 0 if s.lower().strip().startswith('m') else 1

def set_attributes( obj, attributes ):
	changed = False
	for key, value in attributes.iteritems():
		if getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def large_delete_all( Object ):
	while Object.objects.count():
		with transaction.atomic():
			ids = Object.objects.values_list('pk', flat=True)[:999]
			Object.objects.filter(pk__in = ids).delete()

def to_int_str( v ):
	try:
		return unicode(long(v))
	except:
		pass
	return toUnicode(v)
		
def to_str( v ):
	return toUnicode(v)

fnameDefault = r'EV\CyclingBC_28_Mar_2014_EV-Race-List.xls'
def init_ccn( fname = fnameDefault ):
	global datemode
	
	#large_delete_all( LicenseHolder )
	#large_delete_all( Team )
	
	tstart = datetime.datetime.now()
	
	discipline_id = dict( (discipline, Discipline.objects.get(name=discipline)) for discipline in ['Road', 'Track', 'Cyclocross', 'MTB'] )

	effective_date = datetime.date.today()
	
	# Process the records in large transactions for efficiency.
	@transaction.atomic
	def process_ur_records( ur_records ):
		
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_value( ur.get('DOB', '') )
			except Exception as e:
				print 'Row {}: Invalid birthdate "{}" ({}) {}'.format( i, ur.get('DOB',''), ur, e )
				continue
				
			if not ur.get('License Numbers',''):
				print 'Row {}: Missing License Code '.format(i)
				continue
			
			attributes = {
				'license_code':	to_int_str(ur.get('License Numbers','')),
				'last_name':	to_str(ur.get('Last Name','')).strip(),
				'first_name':	to_str(ur.get('First Name','')).strip(),
				'gender':		gender_from_str(to_str(ur.get('Sex','m'))),
				'date_of_birth':date_of_birth,
				'city':			to_str(ur.get('Member City','')).strip(),
				'state_prov':	to_str(ur.get('Member Province','')).strip(),
				'nationality':  to_str(ur.get('Nationality','')).strip(),
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
			
			print u'{:>6}: {:>8} {:>10} {}, {}, {}, {}'.format(
				i,
				removeDiacritic(lh.license_code),
				lh.date_of_birth.strftime('%Y/%m/%d'),
				lh.uci_code,
				removeDiacritic(lh.last_name), removeDiacritic(lh.first_name),
				removeDiacritic(lh.city), removeDiacritic(lh.state_prov) )
			TeamHint.objects.filter( license_holder=lh ).delete()
			
			teams = [t.strip() for t in ur.get('Afiliates','').split(',')]
			if teams:
				last_team = None
				for t in teams:
					team = Team.objects.get_or_create( name=t )[0]
					last_team = team
				pcd = ur.get('Primary Cycling Discipline','').strip().lower()
				for id, d in discipline_id.iteritems():
					if d.name.lower() in pcd:
						TeamHint( discipline=d, license_holder=lh, effective_date=effective_date, team=last_team )
						break
				
	suffix = 'CCN'
	ur_records = []
	wb = open_workbook( fname )
	datemode = wb.datemode
	
	ws = None
	for sheet_name in wb.sheet_names():
		if sheet_name.endswith(suffix):
			print 'Reading sheet: {}'.format(sheet_name)
			ws = wb.sheet_by_name(sheet_name)
			break
	
	if not ws:
		print 'Cannot find sheet ending with "{}"'.format(suffix)
		return
		
	num_rows = ws.nrows
	num_cols = ws.ncols
	for r in xrange(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [toUnicode(f.value).strip() for f in row]
			print '\n'.join( fields )
			continue
			
		ur = dict( (f, row[c].value) for c, f in enumerate(fields) )
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 3000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	print 'Initialization in: ', datetime.datetime.now() - tstart
