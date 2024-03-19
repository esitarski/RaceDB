import os
import sys
import datetime
from django.core.management.base import BaseCommand, CommandError
from core.views import backup_create

class Command(BaseCommand):
	
	help = 'Create a RaceDB database'
	
	def add_arguments(self, parser):
		parser.add_argument('backup_filename', nargs='?', help='name of backup file ending in .json.gz')
					
	def handle(self, *args, **options):
		backup_filename = options['backup_filename']
		if not backup_filename:
			backup_filename = os.path.join( 'backups', 'RaceDB-Backup-{}.json.gz'.format( datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') ) )
		dir_name = os.path.dirname( backup_filename )
		if dir_name:
			os.makedirs( dir_name, exist_ok=True )
		
		print( 'Creating: {} ...'.format(backup_filename) )
		backup_create( backup_filename )
