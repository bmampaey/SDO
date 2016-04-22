#!/usr/bin/env python
from datetime import timedelta
from celery.schedules import crontab


celery_beat_schedule = {
	'execute_data_download_requests': {
		'task': 'tasks.data_request_tasks.execute_data_download_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_delete_requests': {
		'task': 'tasks.data_request_tasks.execute_data_delete_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_data_location_requests': {
		'task': 'tasks.data_request_tasks.execute_data_location_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'execute_metadata_update_requests': {
		'task': 'tasks.data_request_tasks.execute_metadata_update_requests',
		'schedule': timedelta(minutes=5),
		'args': ()
	},
	'curate_export_data_requests': {
		'task': 'tasks.user_request_tasks.curate_export_data_requests',
		'schedule': timedelta(minutes=1),
		'args': ()
	},
#	'sanitize_local_data_location': {
#		'task': 'tasks.data_management_tasks.sanitize_local_data_location',
#		'schedule': crontab(hour=18, minute=0, day_of_week='saturday'),
#		'args': ()
#	},
	'create_AIA_HMI_1H_synoptic_tree': {
		'task': 'tasks.data_management_tasks.create_AIA_HMI_synoptic_tree',
		'schedule': crontab(hour=23, minute=0),
		'args': ("AIA_HMI_1H_synoptic",)
	},
}

