#!/usr/bin/env python
import os
import sys
from helptxt.version import version
try:
	import __builtin__
	__builtin__.__dict__['RaceDBVersion'] = version
except:
	import builtins
	builtins.__dict__['RaceDBVersion'] = version

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RaceDB.settings")
    sys.stderr.write( 'RaceDBVersion={}\n'.format(RaceDBVersion) )
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    
    import django
    assert django.VERSION[:3] >= (1,9,9), "Django version must be >= 1.9.9 (currently {}).".format(django.__version__)
	
    from django.conf import settings
    sys.stderr.write( 'ServerTimeZone="{}"\n'.format(settings.TIME_ZONE) )
    sys.stderr.write( 'python="{}"\n'.format(sys.version) )
    
    execute_from_command_line(sys.argv)
