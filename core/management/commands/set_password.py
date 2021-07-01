import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.create_users import create_users

class Command(BaseCommand):
	
	help = 'Set the login password for RaceDB roles'
	
	def add_arguments(self, parser):
		parser.add_argument('username', help='username')
		parser.add_argument('password', help='password ("none" for no password)')
					
	def handle(self, *args, **options):
		create_users()
		
		username, password = options['username'], options['password']
		if password.lower() == 'none':
			password = None
		
		try:
			user = User.objects.get( username__exact=username )
		except User.DoesNotExist:
			sys.stderr.write( 'username: "{}" not found.  Must be "super", "reg" or "serve"\n'.format(username) )
			return
			
		user.set_password( password )
		user.save()
