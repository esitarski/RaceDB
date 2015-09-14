
import re
import os
import sys
import locale
import datetime
import StringIO
import utils
import scramble
import minimal_intervals

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from models import *

import xlsxwriter

data_headers = (
	'Bib#',
	'LastName', 'FirstName',
	'Team',
	'Nat.', 'StateProv', 'City',
	'Category', 'Age', 'Gender',
	'License', 'UCICode',
	'Tag', 'Tag2',
)

category_headers = (
	'Category Type',
	'Name',
	'Gender',
	'Numbers',
	'Start Offset',
	'Race Laps',
	'Race Distance',
	'Race Minutes',
)

property_headers = (
	'Event Name',
	'Event Organizer',
	'Event City',
	'Event StateProv',
	'Event Country',
	'Event Date',
	'Scheduled Start',
	'Race Number',
	'Race Discipline',
	'Enable RFID',
	'Distance Unit',
	'Time Trial',
	'RFID Option',
	
	'FTP Host',
	'FTP User',
	'FTP Password',
	'FTP Path',
	'FTP Upload During Race',
	
	'GATrackingID',
	'Road Race Finish Times',
)
	
def get_number_range_str( numbers ):
	# Combine consecutive numbers into range pairs.
	numbers = sorted( set(numbers) )
	if len(numbers) <= 1:
		return u','.join( unicode(n) for n in numbers )
	pairs = [(numbers[0], numbers[0])]
	for n in numbers[1:]:
		if n == pairs[-1][1] + 1:
			pairs[-1] = (pairs[-1][0], n)
		else:
			pairs.append( (n, n) )
	return u','.join( unicode(p[0]) if p[0] == p[1] else u'{}-{}'.format(*p) for p in pairs )

def get_gender_str( g ):
	return [u'Men', u'Women', u'Open'][g]

def write_row_data( ws, row, row_data, format = None ):
	if format is None:
		for col, d in enumerate(row_data):
			ws.write( row, col, d )
	else:
		if isinstance(format, list):
			col_format = { col:f for col, f in enumerate(format) }
			default_format = None
		else:
			col_format = {}
			default_format = format
		
		for col, d in enumerate(row_data):
			f = col_format.get(col, default_format)
			if f is not None:
				ws.write( row, col, d, f )
			else:
				ws.write( row, col, d )
	return row + 1

def add_categories_page( wb, title_format, event ):
	#---------------------------------------------------------------------------------------------------
	# Category information.
	#
	ws = wb.add_worksheet('--CrossMgr-Categories')
	
	participant_categories = set( p.category for p in Participant.objects.filter(competition = event.competition) )
	
	exclude_empty_categories = SystemInfo.get_exclude_empty_categories()
	
	# Get some more reasonable number ranges for the categories.
	def get_category_intervals():
		cat_sequence = []
		numbers = []
		for wave in event.get_wave_set().all():
			categories = set( c for c in wave.categories.all() if c in participant_categories ) if exclude_empty_categories else wave.categories.all()
			categories = sorted( categories, key = lambda c: c.sequence )
			if not categories:
				continue
			participants = list( wave.get_participants_unsorted() )
			for category in categories:
				numbers.append( set(p.bib for p in participants if p.category == category and p.bib) )
				cat_sequence.append( category )
		
		intervals = [minimal_intervals.interval_to_str(i) for i in minimal_intervals.minimal_intervals(numbers)]
		return {c:i for c, i in zip(cat_sequence,intervals)}
	
	category_intervals = get_category_intervals()
	
	row = write_row_data( ws, 0, category_headers, title_format )
	for wave in event.get_wave_set().all():
	
		categories = set( c for c in wave.categories.all() if c in participant_categories ) if exclude_empty_categories else wave.categories.all()
		categories = sorted( categories, key = lambda c: c.sequence )
		if not categories:
			continue
		
		participants = list( wave.get_participants_unsorted() )
		if len(categories) == 1 or event.event_type == 1:	# If only one category, or if this is a time trial, do not output Component waves.
			for category in categories:
				row_data = [
					u'Wave',
					category.code,
					get_gender_str(category.gender),
					#get_number_range_str( p.bib for p in participants if p.category == category and p.bib ),
					category_intervals.get(category,''),
					unicode(getattr(wave,'start_offset',u'')),
					wave.laps if wave.laps else u'',
					wave.distance if wave.distance else u'',
					getattr(wave, 'minutes', None) or u'',
				]
				row = write_row_data( ws, row, row_data )
		else:
			genders = list( set(c.gender for c in categories) )
			row_data = [
				u'Wave',
				wave.name,
				get_gender_str( 2 if len(genders) != 1 else genders[0] ),
				u'',	# No ranges here - these come from the categories.
				unicode(getattr(wave,'start_offset',u'')),
				wave.laps if wave.laps else u'',
				wave.distance if wave.distance else u'',
				getattr(wave, 'minutes', None) or u'',
			]
			row = write_row_data( ws, row, row_data )
			
			for category in categories:
				row_data = [
					u'Component',
					category.code,
					get_gender_str(category.gender),
					#get_number_range_str( p.bib for p in participants if p.category == category and p.bib ),
					category_intervals.get(category,''),
					unicode(getattr(wave,'start_offset',u'')),
					u'',
					u'',
					u'',
				]
				row = write_row_data( ws, row, row_data )

def add_properties_page( wb, title_format, event, raceNumber ):
	competition = event.competition
	
	server_date_time = timezone.localtime(event.date_time)
	
	ws = wb.add_worksheet('--CrossMgr-Properties')
	row = write_row_data( ws, 0, property_headers, title_format )
	row_data = [
		u'-'.join( [competition.name, event.name] ),
		competition.organizer,
		competition.city,
		competition.stateProv,
		competition.country,
		server_date_time.strftime( '%Y-%m-%d' ),
		server_date_time.strftime( '%H:%M' ),
		raceNumber,
		competition.discipline.name,
		competition.using_tags,
		['km', 'miles'][competition.distance_unit],
		True if event.event_type == 1 else False,		# Time Trial
		event.rfid_option,
		
		competition.ftp_host,
		competition.ftp_user,
		scramble.encode(utils.removeDiacritic(competition.ftp_password)),
		competition.ftp_path,
		competition.ftp_upload_during_race,
		
		competition.ga_tracking_id,
		event.road_race_finish_times,
	]
	row = write_row_data( ws, row, row_data )

def get_crossmgr_excel( event_mass_start ):
	competition = event_mass_start.competition

	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	#---------------------------------------------------------------------------------------------------
	# Competitor data
	#
	ws = wb.add_worksheet('Registration')
	
	table = [list(data_headers)] if competition.using_tags else [list(data_headers[:-2])]
	
	categories = sorted( set.union( *[set(w.categories.all()) for w in event_mass_start.get_wave_set().all()] ), key = lambda c: c.sequence )
	for p in event_mass_start.get_participants():
		row_data = [
			p.bib if p.bib else '',
			p.license_holder.last_name, p.license_holder.first_name,
			p.team.name if p.team else '',
			p.license_holder.nationality, p.license_holder.state_prov, p.license_holder.city,
			p.category.code, competition.competition_age(p.license_holder), get_gender_str(p.license_holder.gender),
			p.license_holder.license_code_export, p.license_holder.uci_code,
		]
		if competition.using_tags:
			row_data.extend( [p.tag, p.tag2] )
			
		table.append( row_data )
	
	# Remove empty columns.  Keep Bib column.
	for col in xrange(len(table[0])-1, 0, -1):
		if not any( table[row][col] for row in xrange(1, len(table)) ):
			for row in xrange(0, len(table)):
				del table[row][col]
	
	# Write the rider data.
	write_row_data( ws, 0, table[0], title_format )
	for row in xrange(1, len(table)):
		write_row_data( ws, row, table[row] )
	
	table = None
	
	add_categories_page( wb, title_format, event_mass_start )
	
	raceNumber = 1
	for ms in competition.eventmassstart_set.all():
		if ms == event_mass_start:
			break
		raceNumber += 1
	add_properties_page( wb, title_format, event_mass_start, raceNumber )
	
	wb.close()
	return output.getvalue()

#------------------------------------------------------------------------------------------------

def get_crossmgr_excel_tt( event_tt ):
	competition = event_tt.competition

	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	time_format = wb.add_format( dict(num_format='h:mm:ss') )
	
	#---------------------------------------------------------------------------------------------------
	# Competitor data
	#
	ws = wb.add_worksheet('Registration')
	
	table = [['StartTime'] + list(data_headers)] if competition.using_tags else [['StartTime'] + list(data_headers[:-2])]
	
	categories = sorted( set.union( *[set(w.categories.all()) for w in event_tt.get_wave_set().all()] ), key = lambda c: c.sequence )
	
	participants = list( event_tt.get_participants() )
	start_times = { p: event_tt.get_start_time(p) for p in participants } if event_tt.create_seeded_startlist else {}
	def get_start_time( p ):
		t = start_times.get(p, None)
		return t.total_seconds() if t is not None else 10000.0*60*24*24
	participants.sort( key=lambda p: (get_start_time(p), p.bib or 9999999) )
	
	for p in participants:
		# Convert to Excel time which is a fraction of a day.
		start_time = start_times.get(p, None)
		row_data = [
			start_time.total_seconds() / (24.0*60.0*60.0) if start_time is not None else u'',
			p.bib if p.bib else u'',
			p.license_holder.last_name, p.license_holder.first_name,
			p.team.name if p.team else u'',
			p.license_holder.nationality, p.license_holder.state_prov, p.license_holder.city,
			p.category.code, competition.competition_age(p.license_holder), get_gender_str(p.license_holder.gender),
			p.license_holder.license_code, p.license_holder.uci_code,
		]
		if competition.using_tags:
			row_data.extend( [p.tag, p.tag2] )
			
		table.append( row_data )
	
	# Remove empty columns.  Keep Bib and StartTime column.
	for col in xrange(len(table[0])-1, 1, -1):
		if not any( table[row][col] for row in xrange(1, len(table)) ):
			for row in xrange(0, len(table)):
				del table[row][col]
	
	# Write the rider data.
	write_row_data( ws, 0, table[0], title_format )
	format = [time_format]
	for row in xrange(1, len(table)):
		write_row_data( ws, row, table[row], format )
	
	table = None
	
	add_categories_page( wb, title_format, event_tt )
	
	raceNumber = 1 + competition.eventmassstart_set.all().count()
	for ms in competition.eventtt_set.all():
		if ms == event_tt:
			break
		raceNumber += 1
	add_properties_page( wb, title_format, event_tt, raceNumber )
	
	wb.close()
	return output.getvalue()
