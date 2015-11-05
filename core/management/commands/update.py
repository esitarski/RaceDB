from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import subprocess
import datetime

class Command(BaseCommand):
	def handle(self, *args, **options):
		subprocess.call( ['python', 'dependencies.py', '--upgrade'] )
		call_command( 'migrate' )
		print
		print '**********************************************************'
		print '**** RaceDB updated at {}'.format(datetime.datetime.now())
		print '**** start RaceDB with "python manage.py launch <options>'