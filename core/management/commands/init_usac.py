from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_usac

class Command(BaseCommand):

	help = 'Initialize the database with USAC rider data.  Choose which state to read.'
	
	def add_arguments(self, parser):
		parser.add_argument('fname',
			type=str,
			default='',
			help='import filename.csv')
		parser.add_argument('states', nargs='?',
			type=str,
			default='',
			help='Comma separated list of states to import (eg. "CA,OR,WA"')
					
	def handle(self, *args, **options):
		core.init_usac.init_usac( options['fname'], options['states'] )
