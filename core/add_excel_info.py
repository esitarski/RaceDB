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

def add_excel_info( wb ):
	uname = platform.uname()
	set_custom_property = wb.set_custom_property
	set_custom_property('RaceDB_AppVersion',	'RaceDB {}'.format( RaceDBVersion ))
	set_custom_property('RaceDB_Timestamp',		datetime.datetime.now() )
	set_custom_property('RaceDB_User',			os.getlogin())
	set_custom_property('RaceDB_Python',		sys.version.replace('\n', ' '))
	set_custom_property('RaceDB_Django',		version.get_version())
	set_custom_property('RaceDB_Database',		get_db())
	for a in ('system', 'release', 'version', 'machine', 'processor'):
		set_custom_property( 'RaceDB_' + a.capitalize(), getattr(uname, a, ''))
