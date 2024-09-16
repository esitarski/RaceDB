import io
import xlsxwriter

from .models import *
from .add_excel_info import add_excel_info

data_headers = (
	'Bib', 'Status', 'Date',
	'LastName', 'FirstName',
	'Gender',
	'DOB',
	'City', 'StateProv',
	'License',
	'UCIID',
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

def get_number_set_excel( nses ):
	output = io.BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet('Number Set Bibs')
	
	row = write_row_data( ws, 0, data_headers, title_format )
	for nse in nses:
		lh = nse.license_holder
		data = [
			nse.bib,
			'Lost' if nse.date_lost else 'Held',
			nse.date_lost.strftime('%Y-%m-%d') if nse.date_lost else '',
			lh.last_name,
			lh.first_name,
			lh.get_gender_display(),
			lh.date_of_birth.strftime('%Y-%m-%d'),
			lh.city,
			lh.state_prov,
			lh.license_code,
			lh.uci_id,
		]
		row = write_row_data( ws, row, data )
	
	add_excel_info( wb )
	
	wb.close()
	return output.getvalue()
