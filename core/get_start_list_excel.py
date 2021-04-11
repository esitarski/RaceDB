import os
import datetime
import xlsxwriter
from django.utils.translation import gettext_lazy as _

from . import utils
from .models import *

data_headers = (
	'Wave',
	'Category',
	'Bib',
	'LastName', 'FirstName',
	'Team',
	'Gender',
	'DOB',
	'City', 'StateProv',
	'License',
	'NatCode',
	'UCIID',
	'Prereg',
	'Paid',
	'SeasonsPass',
	'Confirmed',
	'Note',
)

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

def get_start_list_excel( event ):
	output = BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	time_format = wb.add_format({'num_format': 'HH.MM.SS'})
	
	ws = wb.add_worksheet(utils.cleanExcelSheetName(event.name))
	
	competition = event.competition
	if competition.seasons_pass:
		seasons_pass = set( SeasonsPassHolder.objects.filter( seasons_pass=competition.seasons_pass ).values_list('license_holder__pk', flat=True) )
	else:
		seasons_pass = set()
	
	if event.event_type == 0:
		row = write_row_data( ws, 0, data_headers, title_format )
		for w in event.get_wave_set().all():
			for p in sorted( w.get_participants(), key=lambda p: (p.bib if p.bib else 999999999, p.license_holder.search_text) ):
				lh = p.license_holder
				data = [
					w.name,
					p.category.code if p.category else u'None',
					p.bib if p.bib else 'None',
					lh.last_name, lh.first_name,
					u'{}'.format(p.team_name),
					lh.get_gender_display(),
					lh.date_of_birth.strftime('%Y-%m-%d'),
					lh.city, lh.state_prov,
					lh.license_code, lh.nation_code, lh.get_uci_id_text(),
					p.preregistered,
					p.paid,
					lh.pk in seasons_pass,
					p.confirmed,
					p.note if p.note else u'',
				]
				row = write_row_data( ws, row, data )
	elif event.event_type == 1:
		row = write_row_data( ws, 0, ['Clock', 'Stopwatch'] + list(data_headers)[1:], title_format )
		format_list = [time_format] * 2
		for p in event.get_participants_seeded():
			lh = p.license_holder
			data = [
				timezone.localtime(p.clock_time).strftime('%H:%M:%S') if p.clock_time else p.clock_time,
				p.start_time,
				p.category.code if p.category else u'None',
				p.bib if p.bib else 'None',
				lh.last_name, lh.first_name,
				u'{}'.format(p.team_name),
				lh.get_gender_display(),
				lh.date_of_birth.strftime('%Y-%m-%d'),
				lh.city, lh.state_prov,
				lh.license_code, lh.get_uci_id_text(), lh.nation_code,
				p.preregistered,
				p.paid,
				lh.pk in seasons_pass,
				p.confirmed,
				p.note if p.note else u'',
			]
			row = write_row_data( ws, row, data, format_list )
		
			
	wb.close()
	return output.getvalue()
