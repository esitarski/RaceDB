from django.core.management.base import BaseCommand, CommandError
from core.models import fix_finish_times

class Command(BaseCommand):

	help = 'Fix the finish times'

	def add_arguments(self, parser):
		pass

	def handle(self, *args, **options):
		fix_finish_times()
