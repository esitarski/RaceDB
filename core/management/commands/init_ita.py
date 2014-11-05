from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_ita

class Command(BaseCommand):

	args = '<ccn_sheet.xls>'
	help = 'Initialized the database with USAC CCN data'

	def handle(self, *args, **options):
		core.init_ita.init_ccn( *args )
