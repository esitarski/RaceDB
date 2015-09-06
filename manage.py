#!/usr/bin/env python
import os
import sys
from helptxt.version import version
import __builtin__
__builtin__.__dict__['RaceDBVersion'] = version

if __name__ == "__main__":
    sys.stderr.write( 'RaceDBVersion={}\n'.format(RaceDBVersion) )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RaceDB.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
