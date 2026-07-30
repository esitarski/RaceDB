import io
import xlsxwriter

from .models import *
from .add_excel_info import add_excel_info

data_headers = (
	'Bib',
	'LastName', 'FirstName',
	'Team',
	'Nation',
	'Category',
	'Gender',
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

def get_category_numbers_assign_excel( category_numbers ):
	output = io.BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet('Category Numbers Assign')
	
	headers = list( data_headers ) + [str(t) for t in category_numbers.ranking_titles]
	
	row = write_row_data( ws, 0, headers, title_format )
	for p in category_numbers.get_participants_sorted():
		lh = p.license_holder
		data = [
			p.bib or '',
			lh.last_name,
			lh.first_name,
			p.team.name if p.team else '',
			lh.nation_code,
			p.category.code,
			str(lh.get_gender_display()),
			lh.uci_id if lh.uci_id else '',
		]
		data.extend( (r or '') for r in p.callup_ranks )
		row = write_row_data( ws, row, data )
	
	ws.autofit()

	add_excel_info( wb )
	
	wb.close()
	return output.getvalue()
