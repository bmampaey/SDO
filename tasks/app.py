#!/usr/bin/env python
from __future__ import absolute_import
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")

from celery import Celery
from django.conf import settings
#from djcelery.schedulers import DatabaseScheduler
from tasks.tasks_schedule import celery_beat_schedule

app = Celery('app', broker='amqp://admin:admin@localhost:5672//', backend='redis://localhost:6379/0')

# Optional configuration, see the application user guide.
app.conf.update(
	#CELERY_ACCEPT_CONTENT = ['json'],
	CELERY_TASK_RESULT_EXPIRES=259200,
	CELERY_TRACK_STARTED = True,
	CELERY_ACKS_LATE = True,
	# Avoid memory leak build-up
	CELERYD_MAX_TASKS_PER_CHILD = 10,
	CELERYD_PREFETCH_MULTIPLIER = 1,
	 # To be removed if we set a rate limit on some tasks
	CELERY_DISABLE_RATE_LIMITS = True,
	CELERY_TIMEZONE = 'Europe/Brussels',
	CELERYD_STATE_DB = '/var/run/celery/state.db',
	# Beat tasks are configured through the admin interface
	# But it doesn't work for now, we have to wait fo an update of djcelery
	# CELERYBEAT_SCHEDULER = DatabaseScheduler,
	# In the mean time we use the regular scheduler
	CELERYBEAT_SCHEDULE = celery_beat_schedule,
	CELERYBEAT_SCHEDULE_FILENAME =  '/var/run/celery/celerybeat-schedule.db',
	CELERYBEAT_MAX_LOOP_INTERVAL = 30,
	# Send a mail each time a task fail
	CELERY_SEND_TASK_ERROR_EMAILS = True,
	# Emails settings are overriden by Django email settings.
	ADMINS = settings.ADMINS,
	SERVER_EMAIL = settings.SERVER_EMAIL,
	EMAIL_HOST = settings.EMAIL_HOST,
	DEBUG = True
)

#app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
	print sys.argv
	app.start(argv=[__file__, "worker", "-A", "tasks.app", "-l", "DEBUG", "--autoreload"])
