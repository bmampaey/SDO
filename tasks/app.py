#!/usr/bin/env python
from __future__ import absolute_import
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")

from celery import Celery
from django.conf import settings
from djcelery.schedulers import DatabaseScheduler

app = Celery('app', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Optional configuration, see the application user guide.
app.conf.update(
	#CELERY_ACCEPT_CONTENT = ['json'],
	CELERY_TASK_RESULT_EXPIRES=600,
	CELERY_TRACK_STARTED = True,
	CELERY_ACKS_LATE = True,
	 # To be removed if we set a rate limit on some tasks
	CELERY_DISABLE_RATE_LIMITS = True,
	CELERY_TIMEZONE = 'Europe/Brussels',
	# Beat tasks are configured through the admin interface
	CELERYBEAT_SCHEDULER = DatabaseScheduler,
	# Send a mail each time a task fail
	CELERY_SEND_TASK_ERROR_EMAILS = True,
	# Emails settings are overriden by Django email settings.
	ADMINS = settings.ADMINS,
	SERVER_EMAIL = settings.DEFAULT_FROM_EMAIL,
	EMAIL_HOST = settings.EMAIL_HOST,
)

#app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
	print sys.argv
	app.start(argv=[__file__, "worker", "-A", "PMD.app", "-l", "DEBUG", "--autoreload"])
