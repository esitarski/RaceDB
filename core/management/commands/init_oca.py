from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_oca

class Command(BaseCommand):

	args = '<oca_csv_file>'
	help = 'Initialized the database with USAC rider data'

	def handle(self, *args, **options):
		core.init_oca.init_oca( *args )
