
import re
import os
import locale
import datetime
import StringIO

import utils
from django.utils.translation import ugettext_lazy as _

from models import *

import xlsxwriter

data_headers = (
	'Bib#',
	'LastName', 'FirstName',
	'Team',
	'Nat.', 'StateProv.', 'City',
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
	
def get_crossmgr_excel( event_mass_start ):
	competition = event_mass_start.competition

	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	#---------------------------------------------------------------------------------------------------
	# Competitor data
	#
	ws = wb.add_worksheet('Registration')
	
	def write_row_data( ws, row, row_data, format = None ):
		if format is None:
			for col, d in enumerate(row_data):
				ws.write( row, col, d )
		else:
			for col, d in enumerate(row_data):
				ws.write( row, col, d, format )
		return row + 1
	
	table = [list(data_headers)] if competition.using_tags else [list(data_headers[:-2])]
	
	categories = sorted( set.union( *[set(w.categories.all()) for w in event_mass_start.wave_set.all()] ), key = lambda c: c.sequence )
	for p in Participant.objects.select_related('license_holder').filter(competition = competition, category__in = categories).order_by('bib'):
		row_data = [
			p.bib if p.bib else '',
			p.license_holder.last_name, p.license_holder.first_name,
			p.team.name if p.team else '',
			p.license_holder.nationality, p.license_holder.state_prov, p.license_holder.city,
			p.category.code, competition.competition_age(p.license_holder), get_gender_str(p.license_holder.gender),
			p.license_holder.license_code, p.license_holder.uci_code,
		]
		if competition.using_tags:
			row_data.extend( [p.tag, p.tag2] )
			
		table.append( row_data )
	
	# Remove empty columns.
	for col in xrange(len(table[0])-1, 0, -1):
		if not any( table[row][col] for row in xrange(1, len(table)) ):
			for row in xrange(0, len(table)):
				del table[row][col]
	
	# Write the rider data.
	write_row_data( ws, 0, table[0], title_format )
	for row in xrange(1, len(table)):
		write_row_data( ws, row, table[row] )
	
	table = None
	#---------------------------------------------------------------------------------------------------
	# Category information.
	#
	ws = wb.add_worksheet('--CrossMgr-Categories')
	
	participant_categories = set( p.category for p in Participant.objects.filter(competition = competition) )
	
	row = write_row_data( ws, 0, category_headers, title_format )
	for wave in event_mass_start.wave_set.all():
		categories = set( c for c in wave.categories.all() if c in participant_categories )
		categories = sorted( categories, key = lambda c: c.sequence )
		if not categories:
			continue
		if len(categories) == 1:
			category = categories[0]
			row_data = [
				u'Wave',
				category.code,
				get_gender_str(category.gender),
				get_number_range_str( p.bib for p in
					Participant.objects.filter(competition = competition, category = category) if p.bib ),
				unicode(wave.start_offset),
				wave.laps if wave.laps else u'',
				wave.distance if wave.distance else u'',
				wave.minutes if wave.minutes else u'',
			]
			row = write_row_data( ws, row, row_data )
		else:
			genders = list( set(c.gender for c in categories) )
			row_data = [
				u'Wave',
				wave.name,
				get_gender_str( 2 if len(genders) != 1 else genders[0] ),
				u'',	# No ranges here - these come from the categories.
				unicode(wave.start_offset),
				wave.laps if wave.laps else u'',
				wave.distance if wave.distance else u'',
				wave.minutes if wave.minutes else u'',
			]			
			row = write_row_data( ws, row, row_data )
			
			for category in categories:
				row_data = [
					u'Component',
					category.code,
					category.gender,
					get_number_range_str( p.bib for p in
						Participant.objects.filter(competition = competition, category = category) if p.bib ),
					unicode(wave.start_offset),
					u'',
					u'',
					u'',
				]
				row = write_row_data( ws, row, row_data )
	
	#---------------------------------------------------------------------------------------------------
	# Property information.
	#
	ws = wb.add_worksheet('--CrossMgr-Properties')
	
	row = write_row_data( ws, 0, property_headers, title_format )

	raceNumber = 1
	for ms in competition.eventmassstart_set.all():
		if ms == event_mass_start:
			break
		raceNumber += 1
	row_data = [
		competition.name,
		competition.organizer,
		competition.city,
		competition.stateProv,
		competition.country,
		event_mass_start.date_time.strftime( '%Y-%m-%d' ),
		event_mass_start.date_time.strftime( '%H:%M' ),
		raceNumber,
		competition.discipline.name,
		competition.using_tags,
		['km', 'miles'][competition.distance_unit],
		False,
	]
	row = write_row_data( ws, row, row_data )
	
	wb.close()
	return output.getvalue()
