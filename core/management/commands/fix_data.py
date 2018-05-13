from django.core.management.base import BaseCommand, CommandError

from core.models import models_fix_data

class Command(BaseCommand):
	
	help = 'Fix up database issues'

	def handle(self, *args, **options):
		models_fix_data()
