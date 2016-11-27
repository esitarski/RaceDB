from django.core.management.base import BaseCommand, CommandError

from core.models import *

class Command(BaseCommand):
	
	help = 'Delete all LicenseHolders (for testing).'

	def handle(self, *args, **options):
		LicenseHolder.objects.all().delete()
		print 'LicenseHolder.objects.count() =', LicenseHolder.objects.count()
