import json
import gzip

from django.core.management.base import BaseCommand, CommandError
from core.competition_import_export import license_holder_export

class Command(BaseCommand):
	
	help = 'Export all license holders, include number sets and waivers'
	
	def add_arguments(self, parser):
		pass
					
	def handle(self, *args, **options):
		fname_base = 'license_holders'
		with open( fname_base+'.gz', 'wb' ) as gzip_stream:
			gzip_handler = gzip.GzipFile( filename=fname_base+'.json', mode="wb", fileobj=gzip_stream )
			license_holder_export( gzip_handler )
			gzip_handler.flush()
			gzip_handler.close()
