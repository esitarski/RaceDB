"""
Django settings for RaceDB project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+m^ehjjzj=%rk+9)%zc@y2x%cfwno-$nb+4o(5ttez6kw)9)8w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

LOGIN_URL='/RaceDB/Login/'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'crispy_forms',
    'core',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

from django.conf import global_settings
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'core.context_processors.standard',
)

ROOT_URLCONF = 'RaceDB.urls'

WSGI_APPLICATION = 'RaceDB.wsgi.application'

# Crispy forms configuration
CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

def get_database_from_args():
	# Check if we already have the database name from the calling process.
	try:
		return os.environ['sqlite3_database_fname']
	except KeyError:
		pass
	
	# Put all commands here where the "--database" parameter is meaningful.
	try:
		if sys.argv[1] not in ('launch','migrate','runserver','dbshell','shell','loaddata','inspectdb','showmigrations',):
			return None
	except IndexError:
		return None
	
	try:
		i = sys.argv.index( '--database' )
	except ValueError:
		return None
	
	# Set the database filename as an environment variable so it works with Django reload.
	try:
		os.environ['sqlite3_database_fname'] = sys.argv[i+1]
	except IndexError:
		raise ValueError('Missing database name')
	
	del sys.argv[i:i+2]		# Remove the --database argument so we don't upset the regular command parameter checks.
	assert os.path.isfile(os.environ['sqlite3_database_fname']), 'Cannot access database file "{}"'.format(os.environ['sqlite3_database_fname'])
	
	return os.environ['sqlite3_database_fname']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': get_database_from_args() or os.path.join(BASE_DIR, 'RaceDB.sqlite3'),
    }
}

try:
	sys.stderr.write( 'databaseFile="{}"\n'.format( DATABASES['default']['NAME'] ) )
except Exception as e:
	pass

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

try:
	import time_zone
	TIME_ZONE = time_zone.TIME_ZONE
except ImportError:
	TIME_ZONE = 'America/Toronto'

USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join( BASE_DIR, 'RaceDB', 'static_root' )

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]
