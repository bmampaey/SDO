#!/usr/bin/env python
from datetime import timedelta
from celery.schedules import crontab


celery_beat_schedule = {
	'execute_data_download_requests': {
		'task': 'PMD.tasks.execute_data_download_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_delete_requests': {
		'task': 'PMD.tasks.execute_data_delete_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_location_requests': {
		'task': 'PMD.tasks.execute_data_location_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_meta_data_update_requests': {
		'task': 'PMD.tasks.execute_meta_data_update_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'sanitize_local_data_location': {
		'task': 'PMD.tasks.sanitize_local_data_location',
		'schedule': crontab(hour=0, minute=0),
		'args': ()
	},
	'create_SDO_synoptic_tree': {
		'task': 'PMD.tasks.create_SDO_synoptic_tree',
		'schedule': crontab(hour=23, minute=0),
		'args': ("1H_synoptic",)
	},
}

