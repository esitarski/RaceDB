from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from core.models import *
import core.init_prereg_oca

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--competition',
			dest='competition_name',
			type="string",
			default='--MissingCompetition--',
			help='Competition to initialize PreReg data into'),
		make_option('--spreadsheet',
			dest='worksheet_name',
			type="string",
			default='--MissingSpreadsheet--',
			help='\n'.join([
				'Name of the Excel spreadsheet in the form: ExcelFile$SheetName.',
				'That is, the FileName (either .xls or xlms) followed by a "$", followed by the Worksheet name.',
				'The Worksheet name is optional - the default is to read the first sheet.',
			])),
		make_option('--replace_all',
			dest='clear_existing',
			action='store_true',
			default=False,
			help='If specified, all existing Participants in the Competition will cleared first.'),
	)

	args = ''
	help = 'Initialize a Competition with prereg data.'

	def handle(self, *args, **options):
		core.init_prereg_oca.init_prereg_oca( options['competition_name'], options['worksheet_name'], options['clear_existing'] )
