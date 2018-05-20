import re
import sys
import gzip
import datetime
from StringIO import StringIO
from django.core.management.base import BaseCommand, CommandError

from core.models import *
from core.competition_import_export import competition_import, get_competition_name_start_date

class Command(BaseCommand):
	
	help = 'Upload a CrossMgr json results file'
	
	def add_arguments(self, parser):
		parser.add_argument('--replace',
			dest='replace',
			action='store_true',
			default=False,
			help='Replace exising Competition',
		)
		parser.add_argument('--template',
			dest='template',
			action='store_true',
			default='False',
			help='Import Competition structure only (no participants)',
		)
		parser.add_argument('--name_date',
			dest='name_date',
			type=str,
			default='',
			help='New name and date for the Competition.  Must be "CompetitionName+YYYY-MM-DD"',
		)
		parser.add_argument('competition_file',
			type=str,
			default='',
			nargs='?',
			help='Competition gzip file exported from RaceDB',
		)
					
	def handle(self, *args, **options):
		safe_print( u'Performing Competition Import.' )
				
		if not options['competition_file']:
			# FIXLATER.  Support pipes.
			safe_print( u'Error: Missing Competition file.' )
			return						
		
		name, start_date = None, None
		if options['name_date']:
			try:
				name, d = options['name_date'].split('+')
			except Exception as e:
				safe_print( u'Error: name_date must be of the form "CompetitionName+YYYY-MM-DD"' )
				return
			if not name:
				safe_print( u'Error: name must note be blank.' )
				return
			if not re.match( r'^\d\d\d\d-\d\d-\d\d$', d ):
				safe_print( u'Error: date must be of the form "YYYY-MM-DD"' )
				return
			try:
				start_date = datetime.date( *[int(f) for f in d.split('-')] )
			except Exception as e:
				safe_print( 'Error: date must be valid ({})'.format(e) )
				return
		
		try:
			if options['competition_file'].endswith('.gzip') or options['competition_file'].endswith('.gz'):
				fs = gzip.GzipFile(filename=options['competition_file'], mode='rb')
			else:
				fs = open(options['competition_file'], 'rb')
		except Exception as e:
			safe_print( u'Error: Cannot read Competition "{}" ({})'.format(options['competition_file'], e) )
			return			

		try:
			name, start_date, pydata = get_competition_name_start_date( stream=fs, name=name, start_date=start_date )
		except Exception as e:
			safe_print( u'Error: Cannot read Competition "{}" ({})'.format(options['competition_file'], e) )
			return			

		try:
			competition = Competition.objects.get( name=name, start_date=start_date )
		except Exception as e:
			competition = None
		
		if competition:
			if options['replace']:
				safe_print( u'Replacing existing Competition "{}", {}'.format(name, start_date) )
				competition.delete()
			else:
				safe_print( u'Error: Competition "{}", {} already exists.  To replace it,  use the "--replace" option.'.format(name, start_date) )
				return			
		
		safe_print( u'Importing: "{}", {} ({} objects)'.format( name, start_date, len(pydata) ) )
		competition_import( pydata=pydata )
		'''
		try:
			competition_import( pydata=pydata )
		except Exception as e:
			safe_print( u'Error: Cannot import Competition "{}", {} ({})'.format(name, start_date, e) )
			return
		'''

		safe_print( u'Success: Imported Competition "{}", {}'.format(name, start_date) )
