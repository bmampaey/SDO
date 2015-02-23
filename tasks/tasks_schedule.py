#!/usr/bin/env python
from datetime import timedelta
from celery.schedules import crontab


celery_beat_schedule = {
	'execute_data_download_requests': {
		'task': 'tasks.execute_data_download_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_delete_requests': {
		'task': 'tasks.execute_data_delete_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_location_requests': {
		'task': 'tasks.execute_data_location_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_metadata_update_requests': {
		'task': 'tasks.execute_metadata_update_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'sanitize_local_data_location': {
		'task': 'tasks.sanitize_local_data_location',
		'schedule': crontab(hour=0, minute=0),
		'args': ()
	},
	'create_SDO_synoptic_tree': {
		'task': 'tasks.create_SDO_synoptic_tree',
		'schedule': crontab(hour=23, minute=0),
		'args': ("1H_synoptic",)
	},
}

