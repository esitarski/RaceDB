
import os
import datetime
import StringIO
import utils

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from models import *

import xlsxwriter

data_headers = (
	'Wave',
	'Category',
	'Bib',
	'LastName', 'FirstName',
	'Gender',
	'DOB',
	'City', 'StateProv',
	'License', 'UCICode',
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
	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet(utils.removeDiacritic(event.name))
	
	competition = event.competition
	if competition.seasons_pass:
		seasons_pass = set( SeasonsPassEntry.objects.filter(seasons_pass=competition.seasons_pass).values_list('license_holder__pk') )
	else:
		seasons_pass = set()
	
	row = write_row_data( ws, 0, data_headers, title_format )
	for w in event.get_wave_set().all():
		for p in sorted( w.get_participants(), key=lambda p: (p.bib if p.bib else 999999999, p.license_holder.search_text) ):
			lh = p.license_holder
			data = [
				w.name,
				p.category.code if p.category else u'None',
				p.bib if p.bib else 'None',
				lh.last_name, lh.first_name,
				lh.get_gender_display(),
				lh.date_of_birth.strftime('%Y-%m-%d'),
				lh.city, lh.state_prov,
				lh.license_code, lh.uci_code,
				p.preregistered,
				p.paid,
				lh.pk in seasons_pass,
				p.confirmed,
				p.note if p.note else u'',
			]
			row = write_row_data( ws, row, data )
			
	wb.close()
	return output.getvalue()
