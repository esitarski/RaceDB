
import os
import datetime
import StringIO
import utils

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from models import *

import xlsxwriter

data_headers = (
	'LastName', 'FirstName',
	'Gender',
	'DOB',
	'City', 'StateProv',
	'License', 'UCICode',
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

def get_seasons_pass_excel( seasons_pass ):
	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet('Pass Holders')
	
	row = write_row_data( ws, 0, data_headers, title_format )
	for sph in SeasonsPassHolder.objects.select_related('license_holder').filter(seasons_pass=seasons_pass):
		lh = sph.license_holder
		data = [
			lh.last_name,
			lh.first_name,
			lh.get_gender_display(),
			lh.date_of_birth.strftime('%Y-%m-%d'),
			lh.city,
			lh.state_prov,
			lh.license_code,
			lh.uci_code,
		]
		row = write_row_data( ws, row, data )
			
	wb.close()
	return output.getvalue()
