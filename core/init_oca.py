import csv
import datetime
import HTMLParser
from collections import namedtuple
from models import *
from django.db import transaction
from django.db.models import Q
import csv, codecs

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

fnameDefault = 'GFRR/April 17.csv'

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

def init_oca( fname = fnameDefault ):
	#large_delete_all( LicenseHolder )
	#large_delete_all( Team )
	
	tstart = datetime.datetime.now()
	
	discipline_id = dict( (discipline, Discipline.objects.get(name=discipline)) for discipline in ['Road', 'Track', 'Cyclocross', 'MTB', 'Para'] )
	discipline_cols = {
		'Road':				['national_road', 'provincial_road'],
		'Cyclocross':		['national_cyclocross', 'provincial_cyclocross'],
		'Track':			['track'],
		'MTB':				['cross_country', 'provincial_cross_country', 'downhill', 'fourx'],
		'Para':				['para_cycling'],
	}
	
	effective_date = datetime.date.today()
	
	html_parser = HTMLParser.HTMLParser()
	
	# Process the records in larger transactions for performance.
	@transaction.atomic
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_str( ur.dob )
			except Exception as e:
				print 'Line {}: Invalid birthdate "{}" ({}) {}'.format( i, ur.dob, ur, e )
				continue
			
			attributes = {
				'license_code':	ur.license,
				'last_name':	ur.last_name,
				'first_name':	ur.first_name,
				'gender':		gender_from_str(ur.sex),
				'date_of_birth':date_of_birth,
				'city':			ur.city,
				'state_prov':	'Ontario',
				'nationality':	'Canada',
				'uci_code':		ur.uci_code,
			}
			if attributes['uci_code'][:3] != 'CAN':
				attributes['nationality'] = ''
			
			try:
				lh = LicenseHolder.objects.get( license_code=ur.license )
				if set_attributes(lh, attributes):
					lh.save()
			
			except LicenseHolder.DoesNotExist:
				lh = LicenseHolder( **attributes )
				lh.save()
			
			print u'{:>6}: {:>8} {:>10} {}, {}, ({})'.format( i, lh.license_code, lh.date_of_birth.strftime('%Y/%m/%d'), lh.last_name, lh.first_name, lh.city )
			
			team_name = ur.club or ur.trade_team
			TeamHint.objects.filter( license_holder=lh ).delete()
			if team_name:
				team_names = [t.strip() for f in team_name.split(',')]
				for count, team_name in enumerate(team_names):
					team = Team.objects.get_or_create( name=team_name )[0]
					if count == len(team_names)-1:
						for discipline_name, discipline in discipline_id.iteritems():
							for col_name in discipline_cols[discipline_name]:
								if getattr(ur, col_name):
									TeamHint( license_holder=lh, team=team, discipline=discipline, effective_date=effective_date ).save()
									break

	ur_records = []
	with open(fname, 'rU') as fp:
		oca_reader = UnicodeReader( fp )
		for i, row in enumerate(oca_reader):
			if i == 0:
				# Get the header fields from the first row.
				fields = [html_parser.unescape(v.strip()).replace('-','_').replace('#','').strip().replace('4', 'four').replace(' ','_').lower() for v in row]
				fields = ['f{}'.format(i) if not f else f.strip() for i, f in enumerate(fields)]
				print '\n'.join( fields )
				oca_record = namedtuple('oca_record', fields)
				continue
			
			ur = oca_record( *[html_parser.unescape(v.strip()) for v in row] )
			
			ur_records.append( (i, ur) )
			if len(ur_records) == 3000:
				process_ur_records( ur_records )
				ur_records = []
			
	process_ur_records( ur_records )
	
	print 'Initialization in: ', datetime.datetime.now() - tstart
