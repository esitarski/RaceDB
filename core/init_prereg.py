import re
import sys
import datetime
from fnmatch import fnmatch
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from collections import namedtuple, defaultdict
from django.db import transaction, IntegrityError
from django.db.models import Q
from large_delete_all import large_delete_all
from FieldMap import standard_field_map, normalize
import import_utils
from import_utils import *
from models import *

from collections import defaultdict
import operator
class TimeTracker( object ):
	def __init__( self ):
		self.startTime = None
		self.curLabel = None
		self.totals = defaultdict( float )
		
	def start( self, label ):
		t = datetime.datetime.now()
		if self.curLabel and self.startTime:
			self.totals[self.curLabel] += (t - self.startTime).total_seconds()
		self.curLabel = label
		self.startTime = t
		
	def end( self ):
		self.start( None )
		
	def __repr__( self ):
		s = []
		for lab, t in sorted( self.totals.iteritems(), key=operator.itemgetter(1), reverse=True ):
			s.append( '{:<50}: {:6.2f}'.format(lab, t) )
		s.append( '' )
		return '\n'.join( s )

def init_prereg(
		competition_name='', worksheet_name='', clear_existing=False,
		competitionId=None, worksheet_contents=None, message_stream=sys.stdout ):

	tt = TimeTracker()
		
	team_lookup = TeamLookup()
		
	tstart = datetime.datetime.now()
	today = datetime.date.today()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def ms_write( s, flush=False ):
			message_stream.write( removeDiacritic(s) )
	else:
		def ms_write( s, flush=False ):
			message_stream.write( unicode(s) )
			sys.stdout.write( removeDiacritic(s) )
			if flush:
				sys.stdout.flush()
	
	fix_bad_license_codes()
	
	if competitionId is not None:
		competition = Competition.objects.get( pk=competitionId )
	else:
		try:
			competition = Competition.objects.get( name=competition_name )
		except Competition.DoesNotExist:
			ms_write( u'**** Cannot find Competition: "{}"\n'.format(competition_name) )
			return
		except Competition.MultipleObjectsReturned:
			ms_write( u'**** Found multiple Competitions matching: "{}"\n'.format(competition_name) )
			return
	
	optional_events = { normalize(event.name):event for event in competition.get_events() if event.optional }
	pattern_optional_events = defaultdict( list )
	
	# Check for duplicate event names.
	event_name_count = defaultdict( int )
	for event in competition.get_events():
		if event.optional:
			event_name_count[event.name] += 1
	for event_name, count in event_name_count.iteritems():
		if count > 1:
			ms_write( u'**** Error: Duplicate Optional Event Name: "{}".  Perferences to Optional Events may not work properly.\n'.format(event_name) )
	
	role_code = {}
	for role_type, roles in Participant.COMPETITION_ROLE_CHOICES:
		role_code.update( { unicode(name).lower().replace(' ','').replace('.',''):code for code, name in roles } )
		
	# Construct a cache to find categories quicker.
	category_code_gender_suffix = re.compile( r'\(Open\)$|\(Men\)$|\(Women\)$' )
	cat_gender = defaultdict( list )
	category_numbers_set = {None: set()}
	for category in Category.objects.filter( format=competition.category_format ).order_by('gender', 'code'):
		cat_gender[category.code].append( (category, category.gender) )
		cn = competition.get_category_numbers( category )
		category_numbers_set[category] = cn.get_numbers() if cn else set()
	
	def get_category( category_code_search, gender_search ):
		category_code_search = category_code_gender_suffix.sub( '', category_code_search ).strip()
		for category, gender in cat_gender.get(category_code_search, []):
			if gender_search == gender or gender == 2:
				return category
		return None
		
	times = defaultdict(float)
	
	has_legal_entity = competition.legal_entity
	ifm = standard_field_map( exclude = ([] if has_legal_entity else ['waiver']) )
	if has_legal_entity:
		waiver_signed_date = competition.legal_entity.waiver_expiry_date + datetime.timedelta(days=1)
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
		
			tt.start( 'get_fields_from_row' )
		
			v = ifm.finder( ur )
			date_of_birth	= v('date_of_birth', None)
			try:
				date_of_birth = date_from_value(date_of_birth)
			except Exception as e:
				ms_write( 'Row {}: Ignoring birthdate (must be YYYY-MM-DD) "{}" ({}) {}'.format(
					i, date_of_birth, ur, e)
				)
				date_of_birth = None
			date_of_birth 	= date_of_birth if date_of_birth != invalid_date_of_birth else None
			
			uci_code = to_str(v('uci_code', None))
			# If no date of birth, get it from the UCI code.
			if not date_of_birth and uci_code and not uci_code.isdigit():
				try:
					date_of_birth = datetime.date( int(uci_code[3:7]), int(uci_code[7:9]), int(uci_code[9:11]) )
				except:
					pass
			
			# If no date of birth, make one up based on the age.
			age = to_int(v('age', None))
			if not date_of_birth and age:
				date_of_birth = date_of_birth_from_age( age, today )
				year_only_dob = True
			else:
				year_only_dob = False
			
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
			if zip_postal:
				zip_postal = validate_postal_code( zip_postal )
			
			preregistered	= to_bool(v('preregistered', True))
			paid			= to_bool(v('paid', None))
			bib				= (to_int(v('bib', None)) or None)
			bib_auto		= (bib is None and unicode(v('bib',u'')).lower() == u'auto')
			tag				= to_int_str(v('tag', None))
			note		 	= to_str(v('note', None))
			team_name		= to_str(v('team', None))
			club_name		= to_str(v('club', None))
			if not team_name:
				team_name = club_name
			category_code   = to_str(v('category_code', None))
			
			est_kmh			= to_float(v('est_kmh', None))
			est_mph			= to_float(v('est_mph', None))
			if est_mph is not None:
				est_kmh = 1.609344 * est_mph
				est_mph = None
			seed_option		= to_str(v('seed_option', None))
			if seed_option is not None:
				seed_option = seed_option.lower()
				if 'early' in seed_option:
					seed_option = 0
				elif 'late' in seed_option:
					seed_option = 2
				elif 'last' in seed_option:
					seed_option = 3
				else:
					seed_option = 1
			
			uci_id			= to_uci_id(v('uci_id', None))
			nation_code		= to_str(v('nation_code', None))
			
			emergency_contact_name = to_str(v('emergency_contact_name', None))
			emergency_contact_phone = to_str(v('emergency_contact_phone', None))
			emergency_medical = to_str(v('emergency_medical', None))
			
			participant_optional_events = []
			for pattern, events in pattern_optional_events.iteritems():
				included = to_bool(v(pattern, False))
				participant_optional_events.extend( (event, included) for event in events )
			
			race_entered    = to_str(v('race_entered', None))
			
			role			= role_code.get( v('role','').lower().replace(' ', '').replace('.', ''), None )
			waiver			= to_bool(v('waiver',None))
			license_checked	= to_bool(v('license_checked',None))
			
			#------------------------------------------------------------------------------
			# Get LicenseHolder.
			#
			license_holder = None
			#with transaction.atomic():
			if True:
				tt.start( 'get_license_holder' )
			
				if uci_id:
					license_holder = LicenseHolder.objects.filter( uci_id=uci_id ).first()
					
				if not license_holder and license_code and license_code.upper() != u'TEMP':
					try:
						license_holder = LicenseHolder.objects.get( license_code=license_code )
					except LicenseHolder.DoesNotExist:
						ms_write( u'**** Row {}: cannot find LicenceHolder from LicenseCode: {}, Name="{}"\n'.format(
							i, license_code, name) )
						continue
				elif not license_holder:
					# No license code.  Try to find the participant by last/first name, [date_of_birth] and [gender].
					# Case insensitive comparison, accents ignored for names.
					q = Q( search_text__startswith=utils.get_search_text([last_name, first_name]) )
					if date_of_birth and date_of_birth != invalid_date_of_birth:
						if year_only_dob:
							q &= Q( date_of_birth__year=date_of_birth.year )
						else:
							q &= Q( date_of_birth=date_of_birth )
					if gender is not None:
						q &= Q( gender=gender )
					
					try:
						license_holder = LicenseHolder.objects.get( q )
					except LicenseHolder.DoesNotExist:
						# No name match.
						# Create a temporary license holder.
						try:
							license_holder = LicenseHolder(
								**{ attr:value for attr, value in {
										'license_code':'TEMP',
										'last_name':last_name,
										'first_name':first_name,
										'gender':gender,
										'date_of_birth':date_of_birth,
										'uci_code':uci_code,
										'nation_code':nation_code,
										'uci_id':uci_id,
										'email':email,
										'phone':phone,
										'city':city,
										'state_prov':state_prov,
										'zip_postal':zip_postal,
										'emergency_contact_name':emergency_contact_name,
										'emergency_contact_phone':emergency_contact_phone,
										'emergency_medical':emergency_medical,
										'existing_tag':tag if competition.use_existing_tags else None,
									}.iteritems() if value is not None
								}
							)
							license_holder.save()
						except Exception as e:
							ms_write( u'**** Row {}: New License Holder Exception: {}, Name="{}"\n'.format(
									i, e, name,
								)
							)
							continue
					except LicenseHolder.MultipleObjectsReturned:
						ms_write( u'**** Row {}: found multiple LicenceHolders matching "Last, First" Name="{}"\n'.format(
								i, name,
							)
						)
						continue
				
				# Update the license_holder record with all new information.
				tt.start( 'update_license_holder' )
				if set_attributes( license_holder, {
						'date_of_birth':date_of_birth
							if not year_only_dob and date_of_birth != invalid_date_of_birth
							else None,
						'uci_code':uci_code,
						'email':email,
						'phone':phone,
						'city':city,
						'state_prov':state_prov,
						'zip_postal':zip_postal,
						'nation_code':nation_code,
						'uci_id':uci_id,
						'emergency_contact_name':emergency_contact_name,
						'emergency_contact_phone':emergency_contact_phone,
						'emergency_medical':emergency_medical,
						'existing_tag':tag if competition.use_existing_tags else None,
					} ):
					try:
						license_holder.save()
					except Exception as e:
						ms_write( u'**** Row {}: Update License Holder Exception: {}, Name="{}"\n'.format(
								i, e, name,
							)
						)
						continue
				
				#------------------------------------------------------------------------------
				# Get Category.  Open categories will match either Gender.
				#
				category = None
				if category_code:
					tt.start( 'get_category_from_code' )
					category = get_category( category_code, license_holder.gender )
					if category is None:
						ms_write( u'**** Row {}: cannot match Category (ignoring): "{}" Name="{}"\n'.format(
							i, category_code, name,
						) )
				
				#------------------------------------------------------------------------------
				# Get Team
				#
				tt.start( 'get_team' )
				team = None
				if Team.is_independent_name(team_name):
					team = None
				else:
					if team_name not in team_lookup:
						msg = u'Row {:>6}: Added team: {}\n'.format(
							i, team_name,
						)
						ms_write( msg )
					team = team_lookup[team_name]
				
				#------------------------------------------------------------------------------
				tt.start( 'get_participant' )
				participant_keys = { 'competition': competition, 'license_holder': license_holder, }
				if category is not None:
					participant_keys['category'] = category
				
				try:
					participant = Participant.objects.get( **participant_keys )
				except Participant.DoesNotExist:
					participant = Participant( **participant_keys )
				except Participant.MultipleObjectsReturned:
					ms_write( u'**** Row {}: found multiple Participants for this license_holder, Name="{}".\n'.format(
						i, name,
					) )
					continue
				
				# First get the defaults based on previous hints and categories.
				tt.start( 'init_participant_defaults' )
				participant.init_default_values()
				
				# Now, override default values with specified ones.
				tt.start( 'override_participant_defaults' )
				for attr, value in (
						('category',category),
						('bib',bib), ('tag',tag), ('note',note),
						('preregistered',preregistered), ('paid',paid), 
						('seed_option',seed_option), ('est_kmh',est_kmh), 
						('role',role),
						('license_checked',license_checked),
					):
					if value is not None:
						setattr( participant, attr, value )
				if team_name:
					participant.team = team

				# Ensure the existing bib number is compatible with the category.
				tt.start( 'update_bib_new_category' )
				participant.update_bib_new_category()
				
				# Only auto-assign a bib only if there isn't one already.
				if bib_auto and not participant.bib:
					tt.start( 'get_bib_auto' )
					bib = participant.get_bib_auto()
				
				# If we have an assigned bib, ensure it is respected.
				tt.start( 'validate_bib' )
				category = participant.category		# Finalize the category if it has a default value.
				if bib and bib in category_numbers_set[participant.category]:
					participant.bib = bib
					# Add the assigned bib to the number set if it exists.
					if competition.number_set:
						competition.number_set.assign_bib( participant.license_holder, participant.bib )

				# Do a final check for bib compatibility.
				if participant.bib and participant.bib not in category_numbers_set[participant.category]:
					participant.bib = None
				
				participant.preregistered = True
				
				tt.start( 'participant_save' )
				try:
					participant.save()
				except IntegrityError as e:
					ms_write( u'**** Row {}: Error={}\nBib={} Category={} License={} Name="{}"\n'.format(
						i, e,
						bib, category_code, license_code, name,
					) )
					success, integrity_error_message, conflict_participant = participant.explain_integrity_error()
					if success:
						ms_write( u'{}\n'.format(integrity_error_message) )
						ms_write( u'{}\n'.format(conflict_participant) )
					continue
				
				tt.start( 'add_to_default_optional_events' )
				participant.add_to_default_optional_events()
				
				if participant_optional_events:
					participant_optional_events = {
						event:(included and event.could_participate(participant))
						for event, included in participant_optional_events
					}
					option_included = { event.option_id:included for event, included in participant_optional_events.iteritems() }
					ParticipantOption.sync_option_ids( participant, option_included )
					override_events_str = u' ' + u', '.join(
						u'"{}"={}'.format(event.name, included) for event, included in sorted(participant_optional_events.iteritems())
					)
				else:
					override_events_str = ''
				
				if waiver is not None:
					tt.start( 'waiver' )
					if waiver:
						participant.sign_waiver_now( waiver_signed_date )
					else:
						participant.unsign_waiver_now()
						
				tt.end()
				
				ms_write( u'Row {row:>6}: {license:>8} {dob:>10} {uci}, {lname}, {fname}, {city}, {state_prov} {ov}\n'.format(
							row=i,
							license=license_holder.license_code,
							dob=license_holder.date_of_birth.strftime('%Y-%m-%d'),
							uci=license_holder.uci_code,
							lname=license_holder.last_name,
							fname=license_holder.first_name,
							city=license_holder.city,
							state_prov=license_holder.state_prov,
							ov=override_events_str,
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
			ms_write( u'Reading sheet: {}\n'.format(cur_sheet_name) )
			ws = wb.sheet_by_name(cur_sheet_name)
			break
	
	if not ws:
		ms_write( u'Cannot find sheet "{}"\n'.format(sheet_name) )
		return
		
	num_rows = ws.nrows
	num_cols = ws.ncols
	for r in xrange(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [unicode(v.value).strip() for v in row]
			
			# Add all Optional Event patterns.
			for field in fields:
				try:
					pattern = normalize( field )
				except:
					continue
				for event_name, event in optional_events.iteritems():
					if fnmatch(event_name, pattern):
						pattern_optional_events[pattern].append( event )
			for pattern in pattern_optional_events.iterkeys():
				ifm.set_aliases( pattern, (pattern,) )
			
			ifm.set_headers( fields )
			ms_write( u'Header Row:\n' )
			for col, f in enumerate(fields, 1):
				if f.lower().strip() in optional_events:
					ms_write( u'        {}. {} (Optional Event)\n'.format(col,f) )
				else:
					name = ifm.get_name_from_alias( f )
					if name is not None:
						ms_write( u'        {}. {} --> {}\n'.format(col, f, name) )
					else:
						ms_write( u'        {}. ****{} (Ignored)\n'.format(col, f) )
			
			fields_lower = [f.lower() for f in fields]
			if clear_existing or 'bib' in ifm:
				ms_write( u'Recording previous license checkes...\n' )
				if competition.report_label_license_check:
					tt.start( 'license_check_state_refresh' )
					LicenseCheckState.refresh()
	
				ms_write( u'Clearing existing Participants...\n' )
				tt.start( 'clearing_existing_participants' )
				large_delete_all( Participant, Q(competition=competition) )
			
			if 'license_code' not in ifm and 'uci_id' not in ifm:
				ms_write( u'Header Row must contain one of (or both) License or UCI ID.  Aborting.\n' )
				return
			
			ms_write( u'\n' )
			continue
			
		ur_records.append( (r+1, [v.value for v in row]) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	ms_write( u'\n' )
	for section, total in sorted( times.iteritems(), key = lambda e: e[1], reverse=True ):
		ms_write( u'{}={:.6f}\n'.format(section, total) )
	ms_write( u'\n' )
	ms_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
	ms_write( u'\n' )
	ms_write( tt.__repr__() )
