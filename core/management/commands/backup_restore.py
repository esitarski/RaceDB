import sys
from django.core.management.base import BaseCommand, CommandError
from core.views import backup_restore

class Command(BaseCommand):
	
	help = 'Restore a RaceDB database from a backup created with backup_create or downloaded'
	
	def add_arguments(self, parser):
		parser.add_argument('backup_filename', help='name of backup file ending in .json.gz')
		parser.add_argument('--reset_db', action='store_true', help='DROP then CREATE the database, then run migrate ')
		parser.add_argument('--no_input', action='store_true', help='suppress asking for confirmation')
					
	def handle(self, *args, **options):
		backup_filename = options['backup_filename']
		if not options['no_input']:
			if input('Overwrite the current database (type "yes" to continue)? ') != 'yes':
				print( 'Cancelled.' )
				return
		
		status, msg = backup_restore( backup_filename, options['reset_db'] )
		if not status:
			print( 'Failure: {}'.format(msg) )
		else:
			print( 'Success' )
