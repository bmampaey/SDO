#!/usr/bin/python
from __future__ import absolute_import
import sys
sys.path.append('/home/benjmam/SDO')

from celery_app import PMD_app
from celery.contrib.batches import Batches
from celery.utils.log import get_task_logger

from get_config import get_data_sites
from get_data_location import get_drms_data_location, save_drms_data_location, update_request

log = get_task_logger("PMD daemon")

# We need get_data_location tasks to be specialised for each data site
def get_drms_data_location_task_creator(task_name, log, data_location_request_url, timeout = 120, max_attempts = 3, method = "GET", data_location_request_max_size = 100, data_location_request_max_delay = 10):
	'''Create a get_data_location task specialized for a data site'''
	
	# Batch tasks allow to gather queries into one call
	@PMD_app.task(base=Batches, name=task_name, flush_every=data_location_request_max_size, flush_interval=data_location_request_max_delay, track_started = True)
	def get_drms_data_location_task(requests):
		'''Gather the data location queries into one call to get_data_location'''
		
		log.debug("%s: Received %s requests", task_name, len(requests))
		sunums = [request.args[0].sunum for request in requests]
		try:
			results = get_drms_data_location(data_location_request_url, sunums, timeout = timeout, max_attempts = max_attempts, method = method, log = log)
		except Exception, why:
			log.error("Could nor retrieve path for sunums %s at URL %s: %s", sunums, data_location_request_url, str(why))
			for request in requests:
				PMD_app.backend.mark_as_failure(request.id, why)
		else:
			for request in requests:
				try:
					update_request(request.args[0], results[request.args[0].sunum], log = log)
				except Exception, why:
					log.error("Could not update data location request with result: %s", str(why))
					PMD_app.backend.mark_as_failure(request.id, why)
				else:
					PMD_app.backend.mark_as_done(request.id, request.args[0])
	
	return get_drms_data_location_task

# We need save_data_location tasks to be specialised for each data site
def save_drms_data_location_task_creator(task_name, log, data_location_model):
	'''Create a save_drms_data_location task specialized for a data site'''
	
	@PMD_app.task(name=task_name)
	def save_drms_data_location_task(request):
		'''Save the result of a data location request to the DB'''
		log.debug("%s: Received %s", task_name, request)
		return save_drms_data_location(data_location_model, request, log = log)
	return save_drms_data_location_task


# We create the tasks for each data site
get_data_location_tasks = dict()
save_data_location_tasks = dict()
for data_site in get_data_sites():
	get_data_location_tasks[data_site.name] = get_drms_data_location_task_creator(data_site.name + "_get_data_location", log, data_site.data_location_request_url, data_site.data_location_request_timeout, data_site.data_location_request_max_attempts, "GET", data_site.data_location_request_max_size, data_site.data_location_request_max_delay)
	save_data_location_tasks[data_site.name] = save_drms_data_location_task_creator(data_site.name + "_save_data_location", log, data_site.data_location_model)
