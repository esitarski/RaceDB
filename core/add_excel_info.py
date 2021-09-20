import os
import sys
import datetime
import platform
from django.utils import version
from django.conf import settings

def get_db():
	try:
		return settings.DATABASES['default']['ENGINE'].split('.')[-1]
	except Exception:
		return 'unknown'
		
def get_info():
	app = 'RaceDB'
	uname = platform.uname()
	info = {
		'{}_AppVersion'.format(app):	RaceDBVersion,
		'{}_Timestamp'.format(app):		datetime.datetime.now(),
		'{}_User'.format(app):			os.path.basename(os.path.expanduser("~")),
		'{}_Database'.format(app):		get_db(),
		'{}_Python'.format(app):		sys.version.replace('\n', ' '),
	}
	info.update( {'{}_{}'.format(app, a.capitalize()): getattr(uname, a)
		for a in ('system', 'release', 'version', 'machine', 'processor') if getattr(uname, a, '') } )
	return info

def add_excel_info( wb ):
	for k,v in get_info().items():
		wb.set_custom_property( k, v )
