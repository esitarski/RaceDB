from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_ccn

class Command(BaseCommand):

	help = 'Initialize the database with CCN data'

	def add_arguments(self, parser):
		parser.add_argument('fname',
			type=str,
			default='',
			help='import filename.xlsx')

	def handle(self, *args, **options):
		core.init_ccn.init_ccn( options['fname'] )
