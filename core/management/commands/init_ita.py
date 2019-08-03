from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_ita

class Command(BaseCommand):

	help = 'Initialized the database with data'

	def add_arguments(self, parser):
		parser.add_argument('fname',
			type=str,
			default='',
			help='import filename.csv')
	
	def handle(self, *args, **options):
		core.init_ita.init_ccn( optione['fname'] )
