from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_license_holders
from core.init_data import init_data_if_necessary

class Command(BaseCommand):
	args = ''
	help = 'Initialize the database with example license holders'

	def handle(self, *args, **options):
		init_data_if_necessary()
		core.init_license_holders.init_license_holders()
