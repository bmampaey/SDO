#!/usr/bin/env python
from __future__ import absolute_import
import os, errno
import csv
from datetime import datetime, timedelta

from django.template.loader import render_to_string
from django.db import transaction, OperationalError
from celery import group, chord
from celery.utils.log import get_task_logger


from global_config.models import GlobalConfig
from account.models import UserProfile
from PMD.models import DataDownloadRequest, ExportDataRequest, ExportMetadataRequest

from tasks import app, create_link, get_data, update_request_status

log = get_task_logger("SDO")

# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# TODO send mail when too big
@app.task(bind=True)
def execute_export_data_request(self, request, recnums = [], paginator = None):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	#from celery.contrib import rdb; rdb.set_trace()
	
	# Save the task id into the user request to allow easy cancel
	request.task_ids = [self.request.id]
	request.status = "STARTED"
	request.save()
	
	# Create the directory tree
	try:
		os.makedirs(request.export_path)
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Make sure that the request recnums is a list
	if not isinstance(request.recnums, list):
		request.recnums = list()
	
	# Add the recnums to the request
	if paginator is None: # It is a simple request
		request.recnums.extend(recnums)
		request.save()
	
	else: # Add the recnums from the paginator to the request (excluding recnums)
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					if obj.recnum not in recnums:
						request.recnums.append(obj.recnum)
		request.save()
	
	log.debug("Request %s, found %s records to download", request, len(request.recnums))
	
	# To avoid user filling up our system, we check that the request is reasonable
	if request.estimated_size() > request.user.remaining_disk_quota:
		update_request_status(request, "TOO LARGE")
		request.user.send_message('wizard/user_request_toolarge_email_subject.txt', 'wizard/user_request_toolarge_email_content.txt', kwargs = {"request": request}, by_mail = True, copy_to_admins = True)
	
	else:
		# Create all the download and create_link tasks
		for recnum in request.recnums[:]:
			try:
				record = request.data_series.record.objects.get(recnum = recnum)
			except request.data_series.record.DoesNotExist, why:
				log.error("Export data request %s has an invalid recnum %s", request.id, recnum)
				request.recnums.remove(recnum)
			else:
				data_download_request = DataDownloadRequest.create_from_record(record)
				data_download_request.expiration_date = request.expiration_date
				link_path = os.path.join(request.export_path, record.filename)
				async_result = get_data.apply_async((data_download_request,), link = create_link.s(link_path, soft = False, force = True))
				# Save the task id into the request to allow monitoring and easy cancel
				request.task_ids.append(async_result.id)
				request.save()
	
	# Remove self task id from the request
	request.task_ids = request.task_ids[1:]
	request.status = "PROCESSING (%s/%s remaining)" % (len(request.recnums), len(request.recnums))
	request.save()


@app.task
def curate_export_data_requests():
	log.debug("curate_export_data_requests")
	
	request_timeout = GlobalConfig.get("export_data_request_timeout", timedelta(days=40))
	
	# Update each export data request
	# We use the id and not the request itself because it is necessary to lock the request before updating it
	for request_id in ExportDataRequest.objects.filter(status__startswith="PROCESSING").values_list('id', flat=True):
		update_export_data_request.delay(request_id, request_timeout)


@app.task
def update_export_data_request(request_id, request_timeout = timedelta(days=40)):
	log.debug("update_export_data_request %s", request_id)
	
	#from celery.contrib import rdb; rdb.set_trace()
	try:
		# Lock the request to avoid concurrent update (the lock will be released at the first save)
		with transaction.atomic():
			try:
				request = ExportDataRequest.objects.select_for_update(nowait=True).get(id=request_id)
			except ExportDataRequest.DoesNotExist, why:
				log.warning("Request %s was not found, cannot update", request_id)
				return
	
	except OperationalError, why:
		log.warning("Could not lock database row for ExportDataRequest %s: %s", request_id, why)
	
	else:
		# Sort the request tasks by status
		done_tasks, failed_tasks, pending_tasks = [], [], []
		for task_id in request.task_ids:
			result = get_data.AsyncResult(task_id)
			if result.status == "SUCCESS":
				# The task's children must also have a status of success 
				if all(child.status == "SUCCESS" for child in result.children):
					done_tasks.append(task_id)
				elif any(child.status == "FAILURE" for child in result.children):
					failed_tasks.append(task_id)
				else:
					pending_tasks.append(task_id)
			elif result.status in ["PENDING", "STARTED"]:
				pending_tasks.append(task_id)
			else:
				log.error("Task %s has a status of %s", task_id, result.status)
				failed_tasks.append(task_id)
		
		# Some tasks are still pending
		if pending_tasks:
			request.task_ids = pending_tasks + failed_tasks
			# If the request is running for too long we stop it, we update the status and send an email
			if datetime.now() - request.updated > request_timeout:
				request.status = "TIMEOUT (%s/%s missing)" % (len(request.task_ids), len(request.recnums))
				request.save()
				request.revoke()
				request.user.send_message('wizard/user_request_timeout_email_subject.txt', 'wizard/user_request_timeout_email_content.txt', kwargs = {"request": request, "partial": len(request.task_ids) < len(request.recnums)}, by_mail = True, copy_to_admins = True)
			else:
				request.status = "PROCESSING (%s/%s remaining)" % (len(request.task_ids), len(request.recnums))
				request.save()
		# We only have failed tasks left, we update the status and send an email
		elif failed_tasks:
			request.task_ids = failed_tasks
			request.status = "FAILED (%s/%s missing)" % (len(request.task_ids), len(request.recnums))
			request.save()
			errors = [create_link.AsyncResult(task_id).result for task_id in failed_tasks]
			request.user.send_message('wizard/user_request_failure_email_subject.txt', 'wizard/user_request_failure_email_content.txt', kwargs = {"request": request, "partial": len(request.task_ids) < len(request.recnums), "errors":  errors}, by_mail = True, copy_to_admins = True)
		# The tasks are all finished, we update the status and send an email
		else:
			request.task_ids = []
			request.status = "READY"
			request.save()
			request.user.send_message('wizard/user_request_success_email_subject.txt', 'wizard/user_request_success_email_content.txt', kwargs = {"request": request}, by_mail = True, copy_to_admins = True)


@app.task(bind=True)
def execute_export_metadata_request(self, request, recnums = [], paginator = None):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	
	# Save the task id into the user request to allow easy cancel
	request.task_ids = [self.request.id]
	request.status = "STARTED"
	request.save()
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(request.export_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Make sure that the request recnums is a list
	if not isinstance(request.recnums, list):
		request.recnums = list()
	
	# Add the recnums to the request
	if paginator is None: # It is a simple request
		request.recnums.extend(recnums)
		request.save()
	
	else: # Add the recnums from the paginator to the request (excluding recnums)
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					if obj.recnum not in recnums:
						request.recnums.append(obj.recnum)
		request.save()
	
	log.debug("Request %s, found %s records to download", request, len(request.recnums))
	
	# Write the csv file
	try:
		with open(request.export_path, 'wb') as csvfile:
			writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
			columns = request.data_series.get_header_keywords()
			writer.writerow(columns)
			for recnum in request.recnums:
				values = request.data_series.get_header_values(recnum)
				writer.writerow([values[column] for column in columns])
	
	except Exception, why:
		log.error("export_metadata_request %s FAILED: %s", request, why)
		update_request_status(request, "FAILED")
		request.user.send_message('wizard/user_request_failure_email_subject.txt', 'wizard/user_request_failure_email_content.txt', kwargs = {"request": request, "partial": False, "errors":  [why]}, by_mail = True, copy_to_admins = True)
	
	else:
		log.info("export_metadata_request %s SUCCESSFULL. Wrote file to %s ", request, request.export_path)
		request.task_ids = []
		request.status = "READY"
		request.save()
		request.user.send_message('wizard/user_request_success_email_subject.txt', 'wizard/user_request_success_email_content.txt', kwargs = {"request": request}, by_mail = True, copy_to_admins = True)

@app.task
def retry_export_request(request):
	log.debug("retry_export_request request %s", request)
	request.revoke()
	request.task_ids = []
	request.status = "NEW"
	request.save()
	if isinstance(request, ExportDataRequest):
		execute_export_data_request.delay(request)
	elif isinstance(request, ExportMetadataRequest):
		execute_export_metadata_request.delay(request)
	else:
		raise Exception("Unknown request type for %s" % request)
