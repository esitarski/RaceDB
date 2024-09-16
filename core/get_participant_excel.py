import io
import xlsxwriter
from django.utils import timezone

from .models import *
from .add_excel_info import add_excel_info

data_headers = (
	'LastName', 'FirstName',
	'Gender',
	'DOB',
	'City', 'StateProv', 'Nationality',
	'Email',
	'License', 'UCI ID',
	'Emergency Contact', 'Emergency Phone',
	'ZipPostal',
	'Category',
	'Bib',
	'Tag',
	'Team',
	'Role',
	'Confirmed',
	'Paid',
	'License Checked',
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

def get_participant_excel( q = None ):
	q = (q or Q()) & Q( role=Participant.Competitor )
	
	output = io.BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( {'bold': True} )
	
	ws = wb.add_worksheet('Participants')
	
	competition = None
	optional_events = None
	row = None
	
	for p in Participant.objects.filter(q).select_related('license_holder'):
		if competition is None:
			headers = list(data_headers)
			
			competition = p.competition
			
			seasons_pass = competition.seasons_pass
			if seasons_pass:
				headers.append( 'SeasonsPass' )
			
			legal_entity = competition.legal_entity
			if legal_entity:
				headers.append( 'Waiver' )
			optional_events = [e for e in competition.get_events() if e.optional]
			headers.extend( [e.name for e in optional_events] )
			row = write_row_data( ws, 0, headers, title_format )
			
		lh = p.license_holder
		data = [
			lh.last_name,
			lh.first_name,
			lh.get_gender_display(),
			lh.date_of_birth.strftime('%Y-%m-%d'),
			lh.city,
			lh.state_prov,
			lh.nationality,
			lh.email,
			lh.license_code,
			lh.uci_id,
			lh.emergency_contact_name,
			lh.emergency_contact_phone,
			lh.zip_postal,
			p.category.code_gender if p.category else '',
			p.bib if p.bib else '',
			p.tag if p.tag else '',
			p.team.name if p.team else '',
			p.get_role_display(),
			p.confirmed,
			p.paid,
			p.license_checked,
		]
		if seasons_pass:
			data.append( p.is_seasons_pass_holder )
		if legal_entity:
			data.append( p.good_waiver() )
		for e in optional_events:
			data.append( e.is_participating(p) )
		row = write_row_data( ws, row, data )
	
	add_excel_info( wb )
	
	wb.close()
	return output.getvalue()
