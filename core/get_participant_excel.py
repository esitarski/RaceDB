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
	'City', 'StateProv', 'Nationality',
	'Email',
	'License', 'UCICode',
	'Emergency Contact', 'Emergency Phone',
	'ZipPostal',
	'Category',
	'Bib',
	'Tag',
	'Team',
	'Role',
	'Confirmed',
	'Paid',
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
	
	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet('Participants')
	
	competition = None
	optional_events = None
	row = None
	
	row = write_row_data( ws, 0, data_headers, title_format )
	for p in Participant.objects.filter(q).select_related('license_holder'):
		if competition is None:
			headers = list(data_headers)
			
			competition = p.competition
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
			lh.uci_code,
			lh.emergency_contact_name,
			lh.emergency_contact_phone,
			lh.zip_postal,
			p.category.code_gender if p.category else u'',
			p.bib if p.bib else u'',
			p.tag,
			p.team.name if p.team else u'',
			p.get_role_display(),
			p.confirmed,
			p.paid,
		]
		if legal_entity:
			data.append( p.good_waiver() )
		for e in optional_events:
			data.append( e.is_participating(p) )
		row = write_row_data( ws, row, data )
			
	wb.close()
	return output.getvalue()
