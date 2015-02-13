"""
Django settings for SDO project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
import os
import socket
from django.core.exceptions import SuspiciousOperation

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'la!p@+y-oh3c+t0^u!if85y*j&4d6&^-q0=+akce8bk&ixfex='

# To avoid the secret key being sent to github
try:
	from secret_key import *
except ImportError:
	from django.utils.crypto import get_random_string
	import os
	SETTINGS_DIR=os.path.abspath(os.path.dirname(__file__))
	secret_key = get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
	with open(os.path.join(SETTINGS_DIR, 'secret_key.py'), "w") as f:
		f.write("SECRET_KEY = '%s'\n" % secret_key)
	from secret_key import *




# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = [".oma.be"]

# Send security errors to console so that they are logged by apache
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
       'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'account',
    'tastypie',
    'PMD',
    'DRMS',
    'wizard'
)

import djcelery
djcelery.setup_loader()

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'SDO.urls'

WSGI_APPLICATION = 'SDO.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'jsoc_drms',
        'USER': 'production',
        'HOST': 'drmsdb.sdodb.oma.be',
        'PORT': '5432'
    }
}

# Mails config
EMAIL_HOST = "smtp.oma.be"
ADMINS = [("Benjamin Mampaey", "benjamin.mampaey@oma.be")]
SERVER_EMAIL = "SDO_deamon@" + socket.getfqdn(socket.gethostname())
DEFAULT_FROM_EMAIL = "sdoadmin@oma.be"


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Brussels'

USE_I18N = True

USE_L10N = False

USE_TZ = False

SHORT_DATETIME_FORMAT = DATETIME_FORMAT = 'Y-m-d H:i:s'

# Save the session to the database on every single request
# Important, see https://docs.djangoproject.com/en/dev/topics/http/sessions/#when-sessions-are-saved
SESSION_SAVE_EVERY_REQUEST = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Must match the data folder
DATA_URL = '/data/'

DATA_ROOT = '/data'
