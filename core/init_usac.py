import io
import csv
import six
import datetime
from six.moves.html_parser import HTMLParser
from html import unescape
from collections import namedtuple
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError

from .models import *
from .utils import removeDiacritic
from .large_delete_all import large_delete_all

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

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
		print ( yy, mm, dd )
		raise e
		
def gender_from_str( s ):
	return 0 if s.lower().startswith('m') else 1

def set_attributes( obj, attributes ):
	changed = False
	for key, value in attributes.items():
		if getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def init_usac( fname=None, states='' ):
	#large_delete_all( LicenseHolder )
	#large_delete_all( Team )
	
	fname = fname or fnameDefault
	
	tstart = datetime.datetime.now()
	
	fix_bad_license_codes()
	
	state_set = set( states.split(',') ) if states else None

	discipline_id = { discipline.name.lower():discipline for discipline in Discipline.objects.all() }

	effective_date = datetime.date.today()
	
	html_parser = HTMLParser()
	
	# Process the records in larger transactions for performance.
	@transaction.atomic
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			try:
				date_of_birth	= date_from_str( ur.birthdate )
			except Exception as e:
				safe_print( u'Line {}: Invalid birthdate "{}" ({}) {}'.format( i, ur.birthdate, ur, e ) )
				continue
			
			attributes = {
				'license_code':	ur.license.upper().lstrip('0'),
				'last_name':	ur.last_name,
				'first_name':	ur.first_name,
				'gender':		gender_from_str( ur.gender ),
				'date_of_birth':date_of_birth,
				'city':			ur.city,
				'state_prov':	ur.state,
				'nationality': 'USA',
				'uci_code':		ur.uci_code or None,
				'zip_postal':	ur.zip,
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
					safe_print( 'IntegrityError:', attributes )
					continue
			
			safe_print( u'{:>6}: {:>8} {:>10} {}, {} {}'.format( i, lh.license_code, lh.date_of_birth.strftime('%Y/%m/%d'),
				lh.last_name, lh.first_name, lh.state_prov ) )
			
			teams = dict( ((th.discipline, th.team.team_type), th) for th in TeamHint.objects.select_related('team').filter(license_holder=lh, team__isnull=False) )
			th_used = set()
			for code, discipline_name in [('rd', 'Road'), ('track', 'Track'), ('cx', 'Cyclocross'), ('mtn', 'MTB')]:
				discipline_obj = discipline_id.get( discipline_name.lower(), None )
				if not discipline_obj:
					continue
				
				if getattr(ur, code + 'team', None):
					tname = getattr(ur, code + 'team')
					ttype = 1
				elif getattr(ur, code + 'club', None):
					tname = getattr(ur, code + 'club')
					ttype = 0
				else:
					continue
					
				attributes = {
					'discipline':		discipline_obj,
					'license_holder':	lh,
					'effective_date':	effective_date,
					'team':				Team.objects.get_or_create(name=tname, team_type=ttype, nation_code='USA')[0],
				}
				try:
					th = teams[(discipline_obj, ttype)]
					if set_attributes( th, attributes ):
						th.save()
				except KeyError:
					th = TeamHint( **attributes )
					th.save()
				safe_print( u'{} {}: {} ({})'.format( ' '*16,
						discipline_name,
						attributes['team'].name,
						['Club', 'Team'][ttype]
					)
				)
				th_used.add( th )
				
			th_delete = set( teams.values() ) - th_used
			if th_delete:
				TeamHint.objects.filter( id__in = [th.id for th in th_delete] ).delete()

	ur_records = []
	with open(fname, 'r', errors='replace') as fp:
		usac_reader = csv.reader( fp )
		for i, row in enumerate(usac_reader):
			if i == 0:
				# Get the header fields from the first row.
				fields = [unescape(v.strip()).replace(' ','_').replace('#','').lower() for v in row]
				safe_print( u'\n'.join(fields) )
				usac_record = namedtuple('usac_record', fields)
				continue
			
			ur = usac_record( *[unescape(v.strip()) for v in row] )
			if state_set and ur.state not in state_set:
				continue
			
			ur_records.append( (i, ur) )
			if len(ur_records) == 3000:
				process_ur_records( ur_records )
				ur_records = []
			
	process_ur_records( ur_records )
	
	print ( 'Initialization in: {}'.format(datetime.datetime.now() - tstart) )
