
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

def participation_excel( start_date=None, end_date=None, discipline=None, race_class=None ):
	discipline = int(discipline or -1)
	race_class = int(race_class or -1)

	competitions = Competition.objects.all()
	if start_date is not None:
		competitions = competitions.filter( start_date__gte = start_date )
	if end_date is not None:
		competitions = competitions.filter( start_date__lte = end_date )
	if discipline > 0:
		competitions = competitions.filter( discipline__pk = discipline )
	if race_class > 0:
		competitions = competitions.filter( race_class__pk = race_class )
	if organizers:
		competitions = competitions.filter( organizer__in = organizers )
	
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
	
	sheet_name = 'RaceDB-Participation'
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
