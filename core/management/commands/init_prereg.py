from django.core.management.base import BaseCommand, CommandError

from core.models import *
import core.init_prereg

class Command(BaseCommand):
	
	def add_arguments(self, parser):
		parser.add_argument('--competition',
			dest='competition_name',
			type=string,
			default='--MissingCompetition--',
			help='Competition to initialize PreReg data into',
		)
		parser.add_argument('--spreadsheet',
			dest='worksheet_name',
			type=string,
			default='--MissingSpreadsheet--',
			help='\n'.join([
				'Name of the Excel spreadsheet in the form: ExcelFile$SheetName.',
				'That is, the FileName (either .xls or xlms) followed by a "$", followed by the Worksheet name.',
				'The Worksheet name is optional - the default is to read the first sheet.',
			]),
		)
		parser.add_argument('--replace_all',
			dest='clear_existing',
			action='store_true',
			default=False,
			help='If specified, all existing Participants in the Competition will cleared first.',
		)

	help = 'Initialize a Competition with prereg data.'

	def handle(self, *args, **options):
		core.init_prereg.init_prereg( options['competition_name'], options['worksheet_name'], options['clear_existing'] )
