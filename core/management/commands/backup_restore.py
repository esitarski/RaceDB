import sys
from django.core.management.base import BaseCommand, CommandError
from core.views import backup_restore

class Command(BaseCommand):
	
	help = 'Restore a RaceDB database from backup'
	
	def add_arguments(self, parser):
		parser.add_argument('backup_filename', help='name of backup file ending in .json.gz')
		parser.add_argument('--no_input', help='suppress asking for confirmation')
					
	def handle(self, *args, **options):
		backup_filename = options['backup_filename']
		check_input = not options['no_input']
		if check_input:
			if input('Overwrite the current database (type "yes" to continue)? ') != 'yes':
				print( 'Cancelled.' )
				return
		
		print( backup_filename )
		status, msg = backup_restore( backup_filename )
		if not status:
			print( 'Failure: {}'.format(msg) )
		else:
			print( 'Success' )
