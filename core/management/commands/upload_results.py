import json

from django.core.management.base import BaseCommand, CommandError
from core.read_results import read_results_crossmgr
from core.utils import safe_print

class Command(BaseCommand):
	
	help = 'Upload a CrossMgr json results file'
	
	def add_arguments(self, parser):
		parser.add_argument('--json_file',
			dest='json_file',
			type=str,
			help='CrossMgr generated json file to upload')
					
	def handle(self, *args, **options):
		with open( options['json_file'], 'rb' ) as fp:
			payload = json.load( fp )
		result = read_results_crossmgr( payload )
		if result['errors']:
			safe_print( 'Upload FAILED.  Errors.' )
			for e in result['errors']:
				safe_print( '    Error:', e )
		if result['errors']:
			safe_print( 'Upload Succeeded.' )
			for w in result['warnings']:
				safe_print( '    Warning: ', w )
