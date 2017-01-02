"""
WSGI config for RaceDB project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RaceDB.settings")

from core.views_common import set_hub_mode
set_hub_mode( True )

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
