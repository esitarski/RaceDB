import json
import gzip

from django.core.management.base import BaseCommand, CommandError
from core.competition_import_export import license_holder_import

class Command(BaseCommand):
	
	help = 'Export all license holders, include number sets and waivers'
	
	def add_arguments(self, parser):
		parser.add_argument('license_holder_file',
			type=str,
			default='',
			nargs='?',
			help='License Holder gzip file exported from RaceDB',
		)
					
	def handle(self, *args, **options):
		fname = options['license_holder_file']
		if not fname.endswith('.gz') and not fname.endswith('.gzip'):
			fname += '.gz'
		with open( fname, 'rb' ) as gzip_stream:
			gzip_handler = gzip.GzipFile( mode="rb", fileobj=gzip_stream )
			license_holder_import( gzip_handler )
