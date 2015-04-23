from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_oca

class Command(BaseCommand):

	args = '<oca_format_data_file.csv>'
	help = 'Initialize the database with OCA rider data'

	def handle(self, *args, **options):
		core.init_oca.init_oca( *args )
