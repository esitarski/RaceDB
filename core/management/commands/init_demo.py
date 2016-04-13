from django.core.management.base import BaseCommand, CommandError
from core.models import *
import core.init_license_holders

class Command(BaseCommand):
	args = ''
	help = 'Initialize the database with example license holders'

	def handle(self, *args, **options):
		core.init_license_holders.init_license_holders()
