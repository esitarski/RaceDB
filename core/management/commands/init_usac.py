from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_usac

class Command(BaseCommand):

	args = '<usac_csv_file> [AL,CA,NY...]'
	help = 'Initialized the database with USAC rider data'

	def handle(self, *args, **options):
		core.init_usac.init_usac( *args )
