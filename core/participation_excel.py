import io
import xlsxwriter
from django.utils.translation import gettext_lazy as _

from . import utils
from .models import *

def participation_excel( start_date=None, end_date=None, disciplines=None, race_classes=None, organizers=None, include_labels=None, exclude_labels=None  ):
	competitions = Competition.objects.all()
	if start_date is not None:
		competitions = competitions.filter( start_date__gte = start_date )
	if end_date is not None:
		competitions = competitions.filter( start_date__lte = end_date )
	if disciplines:
		competitions = competitions.filter( discipline__pk__in = disciplines )
	if race_classes:
		competitions = competitions.filter( race_class__pk__in = race_classes )
	if organizers:
		competitions = competitions.filter( organizer__in = organizers )
	if include_labels:
		competitions = competitions.filter( report_labels__in = include_labels )
	if exclude_labels:
		competitions = competitions.exclude( report_labels__in = exclude_labels )
	
	p = {}
	events = []
	license_holders = set()
	for competition in competitions:
		if not competition.has_participants():
			continue
		for event in competition.get_events():
			if not event.has_participants():
				continue
			events.append( event )
			for participant in event.get_participants():
				license_holders.add( participant.license_holder )
				p[(participant.license_holder.id, event.id)] = participant
	
	license_holders = sorted( license_holders, key=lambda x: x.get_search_text() )
	events.sort( key=lambda x: x.date_time )
	
	output = io.BytesIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	title_format = wb.add_format( dict(bold=True, text_wrap= True) )
	
	sheet_name = 'RaceDB-Participation'
	ws = wb.add_worksheet(sheet_name)
	
	row = col = 0
	
	ws.write( row, col, '{}'.format(_('Name')), title_format )
	col += 1
	
	ws.write( row, col, '{}'.format(_('Gender')), title_format )
	col += 1
	
	for e in events:
		ws.write( 
			row, col,
			'\n'.join([
				e.competition.name, e.name, e.get_event_type_display(),
				timezone.localtime(e.date_time).strftime('%Y-%m-%d %H:%M')
			]),
			title_format,
		)
		col += 1
	row += 1
	
	for lh in license_holders:
		col = 0
		ws.write( row, col, lh.last_name + ', ' + lh.first_name )
		col += 1
		
		ws.write( row, col, lh.get_gender_display() )
		col += 1
		
		for e in events:
			try:
				participant = p[(lh.id, e.id)]
				ws.write( row, col, participant.category.code_gender if participant.category else '{}'.format(_('Unknown')) )
			except KeyError:
				pass
			col += 1
		row += 1
		
	wb.close()
	return sheet_name, output.getvalue()
