from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_usac

class Command(BaseCommand):

	args = '<usac_file.csv> [AL,CA,NY...]'
	help = 'Initialize the database with USAC rider data.  Choose which state to read.'

	def handle(self, *args, **options):
		core.init_usac.init_usac( *args )
