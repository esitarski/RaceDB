
import re
import os
import sys
import locale
import datetime
import StringIO
import utils

from django.utils.translation import ugettext_lazy as _

from models import *

import xlsxwriter

def participation_excel( year ):
	competitions = Competition.objects.all()
	if year is not None:
		competitions = competitions.filter( start_date__year = year )
	
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
	
	output = StringIO.StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	title_format = wb.add_format( dict(bold=True, text_wrap= True) )
	
	sheet_name = 'RaceDB-Participation-{}'.format( year ) if year is not None else 'RaceDB-Participation'
	ws = wb.add_worksheet(sheet_name)
	
	row = col = 0
	
	ws.write( row, col, unicode(_('Name')), title_format )
	col += 1
	
	ws.write( row, col, unicode(_('Gender')), title_format )
	col += 1
	
	for e in events:
		ws.write( row, col, u'\n'.join([e.competition.name, e.name, e.get_event_type_display(), e.date_time.strftime('%Y-%m-%d %H:%M')]), title_format )
		col += 1
	row += 1
	
	for lh in license_holders:
		col = 0
		ws.write( row, col, lh.last_name + u', ' + lh.first_name )
		col += 1
		
		ws.write( row, col, lh.get_gender_display() )
		col += 1
		
		for e in events:
			try:
				participant = p[(lh.id, e.id)]
				ws.write( row, col, participant.category.code_gender if participant.category else unicode(_('Unknown')) )
			except KeyError:
				pass
			col += 1
		row += 1
		
	wb.close()
	return sheet_name, output.getvalue()
