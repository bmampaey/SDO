#!/usr/bin/env python
from __future__ import absolute_import
from datetime import datetime, timedelta

from django.db import transaction, OperationalError
from celery import group, chord
from celery.utils.log import get_task_logger

from global_config.models import GlobalConfig
from PMD.models import LocalDataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetadataUpdateRequest

log = get_task_logger("SDO")

from tasks import app, update_request_status, get_data, get_data_location, delete_data, update_file_metadata

# TODO add link_error to data requests and remove timeout as we will use soft time outs
@app.task(ignore_result = True)
def execute_data_download_requests():
	log.debug("execute_data_download_requests")
	
	request_timeout = GlobalConfig.get("data_download_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So try to open a transaction and lock the rows in nowait
	try:
		with transaction.atomic():
			for request in DataDownloadRequest.objects.select_for_update(nowait=True).all():
				if request.status == "NEW":
					update_request_status(request, "RUNNING")
					get_data.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
				# If the request is running for too long there could be a problem
				elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
					update_request_status(request, "TIMEOUT")
					app.mail_admins("Request timeout", "The data_download request %s has been running since %s and passed it's timeout %s" % (request.id, request.updated, request_timeout))
			
				elif request.status == "DONE":
					request.delete()
	except OperationalError, why:
		log.warning("Could not lock database rows for DataDownloadRequest: %s", why)


@app.task(ignore_result = True)
def execute_data_location_requests():
	log.debug("execute_data_location_requests")
	
	request_timeout = GlobalConfig.get("data_location_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So try to open a transaction and lock the rows in nowait
	try:
		with transaction.atomic():
			for request in DataLocationRequest.objects.select_for_update(nowait=True).all():
				if request.status == "NEW":
					update_request_status(request, "RUNNING")
					get_data_location.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
				# If the request is running for too long there could be a problem
				elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
					update_request_status(request, "TIMEOUT")
					app.mail_admins("Request timeout", "The data_location request %s has been running since %s and passed it's timeout %s" % (request.id, request.updated, request_timeout))
			
				elif request.status == "DONE":
					request.delete()
	except OperationalError, why:
		log.warning("Could not lock database rows for DataLocationRequest: %s", why)

@app.task(ignore_result = True)
def execute_data_delete_requests():
	log.debug("execute_data_delete_requests")
	
	request_timeout = GlobalConfig.get("data_delete_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So try to open a transaction and lock the rows in nowait
	try:
		with transaction.atomic():
			for request in DataDeleteRequest.objects.select_for_update(nowait=True).all():
				if request.status == "NEW":
					update_request_status(request, "RUNNING")
					delete_data.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
				# If the request is running for too long there could be a problem
				elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
					update_request_status(request, "TIMEOUT")
					app.mail_admins("Request timeout", "The data_delete request %s has been running since %s and passed it's timeout %s" % (request.id, request.updated, request_timeout))
			
				elif request.status == "DONE":
					request.delete()
	except OperationalError, why:
		log.warning("Could not lock database rows for DataDeleteRequest: %s", why)


# TODO check how to get old recnum vs new recnum
# The old file should be deleted from datalocation and disk
@app.task(ignore_result = True)
def execute_metadata_update_requests():
	log.debug("execute_metadata_update_requests")
	
	request_timeout = GlobalConfig.get("metadata_update_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So try to open a transaction and lock the rows in nowait
	try:
		with transaction.atomic():
			for request in MetadataUpdateRequest.objects.select_for_update(nowait=True).all():
				if request.status == "NEW":
					update_request_status(request, "RUNNING")
					# If the recnum is the same we skip
					if request.old_recnum != request.recnum:
						# It is possible the file is not stored locally
						try:
							current_data_location = LocalDataLocation.objects.get(recnum=request.old_recnum)
						except LocalDataLocation.DoesNotExist:
							log.debug("Trying to update meta-data for recnum %s but no data location found", request.old_recnum)
							update_request_status(request, "DONE")
						else:
							# If the file is not really on disk, we cleanup
							if not check_file_exists(current_data_location.path):
								log.info("Cleaning up LocalDataLocation, missing file for %s", data_location)
								current_data_location.delete()
								update_request_status(request, "DONE")
							else:
								# Because meta-data is written in theile, we need to make a copy of the file to break hard links and give it a new name
								new_local_file_path = LocalDataLocation.create_location(request)
								try:
									shutil.copyfile(current_data_location.path, new_local_file_path)
								except IOError, why:
									log.error("Could not copy file %s to %s: %s", current_data_location.path, new_local_file_path, why)
									app.mail_admins("Meta-data update request error", "Request %s\nCould not copy file %s to %s: %s" % (request,current_data_location.path, new_local_file_path, str(why)))
									update_request_status(request, "ERROR")
								else:
									current_data_location.delete()
									update_file_metadata.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
				# If the request is running for too long there could be a problem
				elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
					update_request_status(request, "TIMEOUT")
					app.mail_admins("Request timeout", "The metadata_update request %s has been running since %s and passed it's timeout %s", request.id, request.updated, request_timeout)
			
				elif request.status == "DONE":
					request.delete()
	except OperationalError, why:
		log.warning("Could not lock database rows for MetadataUpdateRequest: %s", why)
