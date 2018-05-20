from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import subprocess
import datetime
from core.utils import safe_print

class Command(BaseCommand):
	def handle(self, *args, **options):
		subprocess.call( ['python', 'dependencies.py', '--upgrade'] )
		call_command( 'migrate' )
		safe_print()
		safe_print( u'**********************************************************' )
		safe_print( u'**** RaceDB updated at {}'.format(datetime.datetime.now()) )
		safe_print( u'**** start RaceDB with "python manage.py launch <options>' )