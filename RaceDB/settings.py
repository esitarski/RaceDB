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

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+m^ehjjzj=%rk+9)%zc@y2x%cfwno-$nb+4o(5ttez6kw)9)8w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

LOGIN_URL='/RaceDB/Login/'
LOGIN_REDIRECT_URL='/RaceDB/Home/'

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
    'crispy_bootstrap3',
    'core',
)

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',
'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'RaceDB.urls'

WSGI_APPLICATION = 'RaceDB.wsgi.application'

# Crispy forms configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap3"
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

try:
	# Pull in a user-defined database if it defined.
	from .DatabaseConfig import DatabaseConfig
	DATABASES = { 'default': DatabaseConfig, }
except ImportError:
	# Otherwise, use the default sqlite3 database.
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': get_database_from_args() or os.path.join(BASE_DIR, 'RaceDB.sqlite3'),
			'OPTIONS': {
				'timeout': 20,	# Increase the timeout to avoid "OperationalError: database is locked" error.
			}
		},
	}

try:
	sys.stderr.write( 'databaseEngine="{}"\n'.format( DATABASES['default']['ENGINE'] ) )
	sys.stderr.write( 'databaseName="{}"\n'.format( DATABASES['default']['NAME'] ) )
except Exception as e:
	pass

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

try:
	from . import time_zone
	TIME_ZONE = time_zone.TIME_ZONE
except ImportError:
	import tzlocal
	TIME_ZONE =  tzlocal.get_localzone().zone

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT=os.path.join(BASE_DIR, 'static')
try:
	from . import StaticUrl
	STATIC_URL = StaticUrl.STATIC_URL
except ImportError:
	STATIC_URL = '/static/'

# Path where media is stored
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
try:
	from . import MediaUrl
except ImportError:
	MEDIA_URL = '/media/'

TEMPLATES = [
{
	'BACKEND': 'django.template.backends.django.DjangoTemplates',
	'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'core', 'templates')],
	'OPTIONS': {
		'debug': True,
		'context_processors': [
			'core.context_processors.standard',
			'django.contrib.auth.context_processors.auth',
			'django.template.context_processors.debug',
			'django.template.context_processors.i18n',
			'django.template.context_processors.media',
			'django.template.context_processors.static',
			'django.template.context_processors.tz',
			'django.template.context_processors.request',
			'django.contrib.messages.context_processors.messages',
		],
		'loaders': [
			('django.template.loaders.cached.Loader', [
				'django.template.loaders.filesystem.Loader',
				'django.template.loaders.app_directories.Loader',
			]),
		],
	},
},	
]

# Disable template caching if development.
if os.path.exists(r'c:\Projects\RaceDBDeploy') or 'home/nloaner' in __file__  or 'home/esitarski/Projects' in __file__:
	TEMPLATES = [{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'APP_DIRS': True,
		'OPTIONS': {
			'debug': True,
			'context_processors': [
				'core.context_processors.standard',
				'django.contrib.auth.context_processors.auth',
				'django.template.context_processors.debug',
				'django.template.context_processors.i18n',
				'django.template.context_processors.media',
				'django.template.context_processors.static',
				'django.template.context_processors.tz',
				'django.template.context_processors.request',
				'django.contrib.messages.context_processors.messages',
			],
		},
	}]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
