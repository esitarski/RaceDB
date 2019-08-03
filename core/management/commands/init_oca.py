from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_oca

class Command(BaseCommand):

	help = 'Initialize the database with OCA rider data'

	def add_arguments(self, parser):
		parser.add_argument('fname',
			type=str,
			default='',
			help='import filename.csv')

	def handle(self, *args, **options):
		core.init_oca.init_oca( optione['fname'] )
