import io
import xlsxwriter
from django.db.models.aggregates import Max

from .models import *
from .add_excel_info import add_excel_info

data_headers = (
	'LastName', 'FirstName',
	'Gender',
	'DOB',
	'City', 'StateProv', 'Nationality',
	'Email',
	'Phone',
	'License',
	'NatCode', 'UCI ID',
	'Emergency Contact', 'Emergency Phone', 'Medical Alert',
	'ZipPostal',
	'SeasonBib',
	'SeasonTag', 'SeasonTag2',
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

def get_license_holder_excel( q = None ):
	q = q or Q()
	
	output = io.BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	
	title_format = wb.add_format( dict(bold = True) )
	
	ws = wb.add_worksheet('LicenseHolders')
	
	#disciplines = list( Discipline.objects.filter(id__in=Competition.objects.all().values_list('discipline',flat=True).distinct() ) )
	disciplines = []
	local_headers = list(data_headers) + ['{} Team'.format(d.name) for d in disciplines]
	
	row = write_row_data( ws, 0, local_headers, title_format )
	for lh in LicenseHolder.objects.filter(q):
		data = [
			lh.last_name,
			lh.first_name,
			lh.get_gender_display(),
			lh.date_of_birth.strftime('%Y-%m-%d'),
			lh.city,
			lh.state_prov,
			lh.nationality,
			lh.email,
			lh.phone,
			lh.license_code,
			lh.nation_code,
			lh.uci_id,
			lh.emergency_contact_name,
			lh.emergency_contact_phone,
			lh.emergency_medical,
			lh.zip_postal,
			lh.existing_bib or '',
			lh.existing_tag or '',
			lh.existing_tag2 or '',
		]
		data.extend( (team.name if team else 'Independent') for team in lh.get_teams_for_disciplines(disciplines) )
		row = write_row_data( ws, row, data )
	
	add_excel_info( wb )
	
	wb.close()
	return output.getvalue()
