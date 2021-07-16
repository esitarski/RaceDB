import os
import pwd
import sys
import datetime
import platform
from django.utils import version
from django.conf import settings

def get_user():
	try:
		return pwd.getpwuid( os.getuid() )[0]
	except Exception:
		return 'unknown'

def get_db():
	try:
		return os.path.basename(settings.DATABASES['default']['NAME'])
	except KeyError:
		return 'unknown'

def add_excel_info( wb ):
	uname = platform.uname()
	wb.set_custom_property('RaceDB_AppVersion',		'RaceDB {}'.format( RaceDBVersion ))
	wb.set_custom_property('RaceDB_Timestamp',		datetime.datetime.now() )
	wb.set_custom_property('RaceDB_User',			get_user())
	wb.set_custom_property('RaceDB_Python',			sys.version.replace('\n', ' '))
	wb.set_custom_property('RaceDB_Django',			version.get_version())
	wb.set_custom_property('RaceDB_Database',		get_db())
	for a in ('system', 'release', 'version', 'machine', 'processor'):
		wb.set_custom_property( 'RaceDB_' + a.capitalize(), getattr(uname, a, ''))
