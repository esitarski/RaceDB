from django.core.management.base import BaseCommand, CommandError

from core.create_users import create_users

class Command(BaseCommand):
	
	help = 'Create standard users (if they do not exist already).'

	def handle(self, *args, **options):
		create_users()
