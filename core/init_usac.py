import csv
import datetime
import HTMLParser
from collections import namedtuple
from models import *
from utils import toUnicode, removeDiacritic
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
import csv, codecs

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [toUnicode(cell) for cell in row]

fnameDefault = 'wp_p_universal.csv'

def date_from_str( s ):
	# Assume month, day, year.
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
	return 0 if s.lower().startswith('m') else 1

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

def init_usac( fname = fnameDefault, states = '' ):
	#large_delete_all( LicenseHolder )
	#large_delete_all( Team )
	
	tstart = datetime.datetime.now()
	
	state_set = set( states.split(',') ) if states else None

	discipline_id = dict( (discipline, Discipline.objects.get(name=discipline)) for discipline in ['Road', 'Track', 'Cyclocross', 'MTB'] )

	effective_date = datetime.date.today()
	
	html_parser = HTMLParser.HTMLParser()
	
	# Process the records in larger transactions for performance.
	@transaction.atomic
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_str( ur.birthdate )
			except Exception as e:
				print 'Line {}: Invalid birthdate "{}" ({}) {}'.format( i, ur.birthdate, ur, e )
				continue
			
			attributes = {
				'license_code':	ur.license.lstrip('0'),
				'last_name':	ur.last_name,
				'first_name':	ur.first_name,
				'gender':		gender_from_str( ur.gender ),
				'date_of_birth':date_of_birth,
				'city':			ur.city,
				'state_prov':	ur.state,
				'nationality': 'USA',
				'uci_code':		ur.uci_code if ur.uci_code else None,
			}
			
			try:
				lh = LicenseHolder.objects.get( license_code=ur.license.lstrip('0') )
				if set_attributes(lh, attributes):
					lh.save()
			
			except LicenseHolder.DoesNotExist:
				lh = LicenseHolder( **attributes )
				try:
					lh.save()
				except IntegrityError:
					print 'IntegrityError:', attributes
					continue
			
			print u'{:>6}: {:>8} {:>10} {}, {} {}'.format( i, lh.license_code, lh.date_of_birth.strftime('%Y/%m/%d'),
				removeDiacritic(lh.last_name), removeDiacritic(lh.first_name), removeDiacritic(lh.state_prov) )
			
			teams = dict( ((th.discipline, th.team.team_type), th) for th in TeamHint.objects.select_related('team').filter(license_holder=lh) )
			th_used = set()
			for code, discipline in [('rd', 'Road'), ('track', 'Track'), ('cx', 'Cyclocross'), ('mtn', 'MTB')]:
				if getattr(ur, code + 'team'):
					tname = getattr(ur, code + 'team')
					ttype = 1
				elif getattr(ur, code + 'club'):
					tname = getattr(ur, code + 'club')
					ttype = 0
				else:
					continue
					
				attributes = {
					'discipline':		discipline_id[discipline],
					'license_holder':	lh,
					'effective_date':	effective_date,
					'team':				Team.objects.get_or_create(name=tname, team_type=ttype, nation_code='USA')[0],
				}
				try:
					th = teams[(discipline_id[discipline], ttype)]
					if set_attributes( th, attributes ):
						th.save()
				except KeyError:
					th = TeamHint( **attributes )
					th.save()
				print u'{} {}: {} ({})'.format( ' '*16,
					removeDiacritic(discipline),
					removeDiacritic(attributes['team'].name),
					['Club', 'Team'][ttype]
				)
				th_used.add( th )
				
			th_delete = set( teams.values() ) - th_used
			if th_delete:
				TeamHint.objects.filter( id__in = [th.id for th in th_delete] ).delete()

	ur_records = []
	with open(fname, 'rU') as fp:
		usac_reader = unicode_csv_reader( fp )
		for i, row in enumerate(usac_reader):
			if i == 0:
				# Get the header fields from the first row.
				fields = [html_parser.unescape(v.strip()).replace(' ','_').replace('#','').lower() for v in row]
				print removeDiacritic( u'\n'.join(fields) )
				usac_record = namedtuple('usac_record', fields)
				continue
			
			ur = usac_record( *[html_parser.unescape(v.strip()) for v in row] )
			if state_set and ur.state not in state_set:
				continue
			
			ur_records.append( (i, ur) )
			if len(ur_records) == 3000:
				process_ur_records( ur_records )
				ur_records = []
			
	process_ur_records( ur_records )
	
	print 'Initialization in: ', datetime.datetime.now() - tstart
