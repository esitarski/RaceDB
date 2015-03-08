import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from collections import namedtuple
from models import *
from django.db import transaction, IntegrityError
from django.db.models import Q
from large_delete_all import large_delete_all
from utils import toUnicode, removeDiacritic

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
	try:
		mm, dd, yy = [int(v.strip()) for v in s.split( '/' )]
	except:
		return datetime.date( 1900, 1, 1 )		# Default date.
	
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
	return 1 if s.lower().strip()[:1] in 'wf' else 0

def set_attributes( obj, attributes ):
	changed = False
	for key, value in attributes.iteritems():
		if getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def to_int_str( v ):
	try:
		return unicode(long(v))
	except:
		pass
	return unicode(v)
		
def to_str( v ):
	if v is None:
		return v
	return toUnicode(v)
	
def to_bool( v ):
	if v is None:
		return None
	s = unicode(v)
	return s[:1] in u'YyTt1'

def to_int( v ):
	if v is None:
		return None
	try:
		return int(v)
	except:
		return None
		
def to_tag( v ):
	if v is None:
		return None
	return unicode(v).split(u'.')[0]

def init_prereg(
		competition_name='', worksheet_name='', clear_existing=False,
		competitionId=None, worksheet_contents=None, message_stream=sys.stdout ):
	global datemode
	
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( unicode(s) )
	
	if competitionId is not None:
		competition = Competition.objects.get( pk=competitionId )
	else:
		try:
			competition = Competition.objects.get( name=competition_name )
		except Competition.DoesNotExist:
			messsage_stream_write( u'Cannot find Competition: "{}"\n'.format(competition_name) )
			return
		except Competition.MultipleObjectsReturned:
			messsage_stream_write( u'Found multiple Competitions matching: "{}"\n'.format(competition_name) )
			return
	
	if clear_existing:
		Participant.objects.filter(competition=competition).delete()
		
	def get_key( d, keys, default_value ):
		for k in keys:
			try:
				return d[k.lower()]
			except KeyError:
				pass
		return default_value
	
	# Process the records in large transactions for efficiency.
	@transaction.atomic
	def process_ur_records( ur_records ):
		
		for i, ur in ur_records:
			license_code	= to_int_str(get_key(ur,('License','License Numbers','LicenseNumbers','License Code','LicenseCode'),u''))
			last_name		= to_str(get_key(ur,('LastName','Last Name'),u'')).strip()
			first_name		= to_str(get_key(ur,('FirstName','First Name'),u'')).strip()
			gender			= gender_from_str(ur.get('Gender'.lower(),u'').strip())
			for alias in ['Date of Birth', 'DOB']:
				v = ur.get(alias.lower(),u'').strip()
				if v:
					date_of_birth	= date_from_value(v)
					break
			preregistered	= to_bool(ur.get('Preregistered'.lower(), True))
			paid			= to_bool(ur.get('Paid'.lower(), None))
			bib				= to_int(ur.get('Bib'.lower(), None))
			tag			 	= to_tag(ur.get('Tag'.lower(), None))
			team_name		= to_str(ur.get('Team'.lower(), None))
			category_code   = to_str(ur.get('Category'.lower(), None))

			if license_code and license_code.upper() != u'TEMP':
				try:
					license_holder = LicenseHolder.objects.get( license_code=license_code )
				except LicenseHolder.DoesNotExist:
					messsage_stream_write( u'Row {}: cannot find LicenceHolder from LicenseCode: {}\n'.format(i, license_code) )
					continue
			else:
				try:
					# No license code.  Try to find the participant by last/first name.
					# Case insensitive comparison.
					license_holder = LicenseHolder.objects.get( last_name__iexact=last_name, first_name__iexact=first_name )
				except LicenseHolder.DoesNotExist:
					# No name match.
					# Create a temporary license holder.
					license_holder = LicenseHolder(
						license_code='TEMP',
						last_name=last_name,
						first_name=first_name,
						gender=gender,
						date_of_birth=date_of_birth )
					license_holder.save()
				except LicenseHolder.MultipleObjectsReturned:
					messsage_stream_write( u'Row {}: found multiple LicenceHolders matching Last,First Name: "{}","{}"\n'.format(
							i, last_name, first_name,
						)
					)
					continue
				
			try:
				participant = Participant.objects.get( competition=competition, license_holder=license_holder )
			except Participant.DoesNotExist:
				participant = Participant( competition=competition, license_holder=license_holder )
			except Participant.MultipleObjectsReturned:
				messsage_stream_write( u'Row {}: found multiple Participants for this competition and license_holder.\n'.format(i) )
				continue
			
			for attr, value in [ ('preregistered',preregistered), ('paid',paid), ('bib',bib), ('tag',tag), ]:
				if value is not None:
					setattr( participant, attr, value )
			
			team = None
			if team_name is not None:
				try:
					team = Team.objects.get(name=team_name)
				except Team.DoesNotExist:
					messsage_stream_write( u'Row {}: unrecognized Team name (ignoring): "{}"\n'.format(
						i, team_name,
					) )
				except Team.MultipleObjectsReturned:
					messsage_stream_write( u'Row {}: multiple Teams match name (ignoring): "{}"\n'.format(
						i, team_name,
					) )
			participant.team = team
			participant.preregistered = True
			
			category = None
			if category_code is not None:
				try:
					category = Category.objects.get( format=competition.category_format, code=category_code )
				except Category.DoesNotExist:
					messsage_stream_write( u'Row {}: unrecognized Category code (ignoring): "{}"\n'.format(
						i, category_code,
					) )
				except Category.MultipleObjectsReturned:
					messsage_stream_write( u'Row {}: multiple Categories match code (ignoring): "{}"\n'.format(
						i, category_code,
					) )
			participant.category = category
			
			participant.init_default_values()
			
			try:
				participant.save()
			except IntegrityError as e:
				messsage_stream_write( u'Row {}: Error={}\nBib={} Category={} License={} Name="{}, {}"\n'.format(
					i, e,
					bib, category_code, license_code, last_name, first_name,
				) )
				success, integrity_error_message, conflict_participant = participant.explain_integrity_error()
				if success:
					messsage_stream_write( u'{}\n'.format(integrity_error_message) )
					messsage_stream_write( u'{}\n'.format(conflict_participant) )
				continue
			
			participant.add_to_default_optonal_events()
			
			messsage_stream_write( u'Row {:>6}: {:>8} {:>10} {}, {}, {}, {}\n'.format(
						i,
						license_holder.license_code, license_holder.date_of_birth.strftime('%Y/%m/%d'), license_holder.uci_code,
						license_holder.last_name, license_holder.first_name,
						license_holder.city, license_holder.state_prov
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
	datemode = wb.datemode
	
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
			messsage_stream_write( u'Headers:\n' )
			for f in fields:
				messsage_stream_write( u'            {}\n'.format(f) )
			
			fields_lower = [f.lower() for f in fields]
			if not any( r.lower() in fields_lower for r in ('License','License Numbers','LicenseNumbers','License Code','LicenseCode') ):
				messsage_stream_write( u'License column not found in Header Row.  Aborting.\n' )
				return
			continue
			
		ur = dict( (f.lower(), row[c].value) for c, f in enumerate(fields) )
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	messsage_stream_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
