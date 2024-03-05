import pytz

from django.utils import timezone
from .models import SystemInfo

class TimezoneMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		system_info = SystemInfo.get_singleton()
		tzname = system_info.tzname
		timezone.activate(pytz.timezone(system_info.tzname))
		return self.get_response(request)
