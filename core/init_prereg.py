import sys
import datetime
from xlrd import open_workbook, xldate_as_tuple
import HTMLParser
from collections import namedtuple, defaultdict
from django.db import transaction, IntegrityError
from django.db.models import Q
from large_delete_all import large_delete_all
import import_utils
from import_utils import *
from models import *

def init_prereg(
		competition_name='', worksheet_name='', clear_existing=False,
		competitionId=None, worksheet_contents=None, message_stream=sys.stdout ):
	
	tstart = datetime.datetime.now()

	if message_stream == sys.stdout or message_stream == sys.stderr:
		def messsage_stream_write( s ):
			message_stream.write( removeDiacritic(s) )
	else:
		def messsage_stream_write( s ):
			message_stream.write( unicode(s) )
	
	fix_bad_license_codes()
	
	if competitionId is not None:
		competition = Competition.objects.get( pk=competitionId )
	else:
		try:
			competition = Competition.objects.get( name=competition_name )
		except Competition.DoesNotExist:
			messsage_stream_write( u'**** Cannot find Competition: "{}"\n'.format(competition_name) )
			return
		except Competition.MultipleObjectsReturned:
			messsage_stream_write( u'**** Found multiple Competitions matching: "{}"\n'.format(competition_name) )
			return
	
	if clear_existing:
		large_delete_all( Participant, Q(competition=competition) )
		
	optional_events = { event.name.lower():event for event in competition.get_events() if event.optional }
		
	times = defaultdict(float)
	
	license_col_names = ('License','License #','License Numbers','LicenseNumbers','License Code','LicenseCode')
	
	# Process the records in large transactions for efficiency.
	def process_ur_records( ur_records ):
		for i, ur in ur_records:
			date_of_birth	= get_key(ur, ('Date of Birth', 'Birthdate', 'DOB'), None)
			try:
				date_of_birth = date_from_value(date_of_birth)
			except:
				print 'Row {}: Invalid birthdate (ignoring) "{}" ({}) {}'.format( i, date_of_birth, ur, e )
				date_of_birth = None
			date_of_birth 	= date_of_birth if date_of_birth != import_utils.invalid_date_of_birth else None
			
			license_code	= to_int_str(get_key(ur, license_col_names, u'')).upper().strip()
			last_name		= to_str(get_key(ur,('LastName','Last Name'),u''))
			first_name		= to_str(get_key(ur,('FirstName','First Name'),u''))
			name			= to_str(ur.get('name',u''))
			if not name:
				name = ' '.join( n for n in [first_name, last_name] if n )
			
			gender			= to_str(get_key(ur,('gender','rider gender'),u''))
			gender			= gender_from_str(gender) if gender else None
			
			email			= to_str(ur.get('email', None))
			city			= to_str(ur.get('city', None))
			state_prov		= to_str(get_key(ur,('state','prov','province','stateprov','state prov'), None))
			zip_postal		= to_str(get_key(ur,('ZipPostal','Zip', 'Postal', 'Zip Code', 'Postal Code', 'ZipCode', 'PostalCode',), None))
			
			preregistered	= to_bool(ur.get('preregistered', True))
			paid			= to_bool(ur.get('paid', None))
			bib				= (to_int(ur.get('bib', None)) or None)
			tag				= to_int_str(get_key(ur,('Tag','Chip'), None))
			note		 	= to_str(ur.get('note', None))
			team_name		= to_str(ur.get('team', None))
			club_name		= to_str(ur.get('club', None))
			if not team_name:
				team_name = club_name
			category_code   = to_str(ur.get('category', None))
			
			emergency_contact_name = to_str(get_key(ur,('Emergency Contact','Emergency Contact Name'), None))
			emergency_contact_phone = to_int_str(get_key(ur,('Emergency Phone','Emergency Contact Phone'), None))
			uci_code = to_str(get_key(ur,('UCI Code','UCICode', 'UCI'), None))
			
			participant_optional_events = {
				optional_events[field]:to_bool(value) for field, value in ur.iteritems() if field in optional_events
			}
			
			#------------------------------------------------------------------------------
			# Get LicenseHolder.
			#
			license_holder = None
			with transaction.atomic():
				if license_code and license_code.upper() != u'TEMP':
					try:
						license_holder = LicenseHolder.objects.get( license_code=license_code )
					except LicenseHolder.DoesNotExist:
						messsage_stream_write( u'**** Row {}: cannot find LicenceHolder from LicenseCode: {}, Name="{}"\n'.format(
							i, license_code, name) )
						continue
				else:
					try:
						# No license code.  Try to find the participant by last/first name.
						# Case insensitive comparison.
						license_holder = LicenseHolder.objects.get( last_name__iexact=last_name, first_name__iexact=first_name )
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
										'email':email,
										'city':city,
										'state_prov':state_prov,
										'zip_postal':zip_postal,
										'emergency_contact_name':emergency_contact_name,
										'emergency_contact_phone':emergency_contact_phone,
										'existing_tag':tag if competition.use_existing_tags else None,
									}.iteritems() if value
								}
							)
							license_holder.save()
						except Exception as e:
							messsage_stream_write( u'**** Row {}: New License Holder Exception: {}, Name="{}"\n'.format(
									i, e, name,
								)
							)
							continue
					except LicenseHolder.MultipleObjectsReturned:
						messsage_stream_write( u'**** Row {}: found multiple LicenceHolders matching "Last, First" Name="{}"\n'.format(
								i, name,
							)
						)
						continue
				
				# Update the license_holder record with all new information.
				if set_attributes( license_holder, {
						'date_of_birth':date_of_birth,
						'uci_code':uci_code,
						'email':email,
						'city':city,
						'state_prov':state_prov,
						'zip_postal':zip_postal,
						'emergency_contact_name':emergency_contact_name,
						'emergency_contact_phone':emergency_contact_phone,
						'existing_tag':tag if competition.use_existing_tags else None,
					} ):
					license_holder.save()
				
				#------------------------------------------------------------------------------
				# Get Category.  Open categories will match either Gender.
				#
				category = None
				if category_code:
					for category_search in Category.objects.filter( format=competition.category_format, code=category_code ).order_by('gender'):
						if category_search.gender == license_holder.gender or category_search.gender == 2:
							category = category_search
							break
					if category is None:
						messsage_stream_write( u'**** Row {}: cannot match Category (ignoring): "{}" Name="{}"\n'.format(
							i, category_code, name,
						) )
				
				#------------------------------------------------------------------------------
				# Get Team
				#
				team = None
				if team_name:
					try:
						team = Team.objects.get(name=team_name)
					except Team.DoesNotExist:
						messsage_stream_write( u'**** Row {}: no Team matches name (ignoring): "{}" Name="{}"\n'.format(
							i, team_name, name,
						) )
					except Team.MultipleObjectsReturned:
						messsage_stream_write( u'**** Row {}: multiple Teams match name (ignoring): "{}" Name="{}"\n'.format(
							i, team_name, name,
						) )
				
				#------------------------------------------------------------------------------
				participant_keys = { 'competition': competition, 'license_holder': license_holder, }
				if category is not None:
					participant_keys['category'] = category
				
				try:
					participant = Participant.objects.get( **participant_keys )
				except Participant.DoesNotExist:
					participant = Participant( **participant_keys )
				except Participant.MultipleObjectsReturned:
					messsage_stream_write( u'**** Row {}: found multiple Participants for this license_holder, Name="{}".\n'.format(
						i, name,
					) )
					continue
				
				for attr, value in (
						('category',category), ('team',team),
						('bib',bib), ('tag',tag), ('note',note),
						('preregistered',preregistered), ('paid',paid), 
					):
					if value is not None:
						setattr( participant, attr, value )
				
				participant.preregistered = True
				
				participant.init_default_values()
				
				try:
					participant.save()
				except IntegrityError as e:
					messsage_stream_write( u'**** Row {}: Error={}\nBib={} Category={} License={} Name="{}"\n'.format(
						i, e,
						bib, category_code, license_code, name,
					) )
					success, integrity_error_message, conflict_participant = participant.explain_integrity_error()
					if success:
						messsage_stream_write( u'{}\n'.format(integrity_error_message) )
						messsage_stream_write( u'{}\n'.format(conflict_participant) )
					continue
				
				participant.add_to_default_optonal_events()
				
				if participant_optional_events:
					participant_optional_events = {
						event:(included and event.could_participate(participant))
						for event, included in participant_optional_events.iteritems()
					}
					option_included = { event.option_id:included for event, included in participant_optional_events.iteritems() }
					ParticipantOption.sync_option_ids( participant, option_included )
					override_events_str = u' ' + u', '.join(
						u'"{}"={}'.format(event.name, included) for event, included in sorted(participant_optional_events.iteritems())
					)
				else:
					override_events_str = ''
				
				messsage_stream_write( u'Row {:>6}: {:>8} {:>10} {}, {}, {}, {}{}\n'.format(
							i,
							license_holder.license_code, license_holder.date_of_birth.strftime('%Y-%m-%d'), license_holder.uci_code,
							license_holder.last_name, license_holder.first_name,
							license_holder.city, license_holder.state_prov,
							override_events_str,
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
				optional_event_str = u' (Optional Event)' if f.lower() in optional_events else u''
				messsage_stream_write( u'            {}{}\n'.format(f, optional_event_str) )
			
			fields_lower = [f.lower() for f in fields]
			if not any( r.lower() in fields_lower for r in license_col_names ):
				messsage_stream_write( u'License column not found in Header Row.  Aborting.\n' )
				return
			continue
			
		ur = { f.strip().lower(): row[c].value for c, f in enumerate(fields) }
		ur_records.append( (r+1, ur) )
		if len(ur_records) == 1000:
			process_ur_records( ur_records )
			ur_records = []
			
	process_ur_records( ur_records )
	
	messsage_stream_write( u'\n' )
	for section, total in sorted( times.iteritems(), key = lambda e: e[1], reverse=True ):
		messsage_stream_write( u'{}={:.6f}\n'.format(section, total) )
	messsage_stream_write( u'\n' )
	messsage_stream_write( u'Initialization in: {}\n'.format(datetime.datetime.now() - tstart) )
