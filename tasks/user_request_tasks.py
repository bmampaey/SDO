#!/usr/bin/env python
from __future__ import absolute_import
import os, errno
import csv

from django.template.loader import render_to_string
from celery import group, chord
from celery.utils.log import get_task_logger


from global_config.models import GlobalConfig
from account.models import UserProfile
from PMD.models import DataDownloadRequest, ExportDataRequest

from tasks import app, create_link, get_data, send_message, update_request_status

log = get_task_logger("SDO")

# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# TODO send mail when too big
@app.task(bind=True)
def execute_export_data_request(self, request, recnums, paginator):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	#from celery.contrib import rdb; rdb.set_trace()
	
	# Save the task id into the user request to allow easy cancel
	update_request_status(request, "STARTED")
	
	# Create the directory tree
	try:
		os.makedirs(request.export_path)
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	if paginator is None: # It is a simple request
		request.recnums = recnums
	
	else: # Add the recnums from the paginator to the request (excluding recnums)
		request.recnums = []
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					if obj.recnum not in recnums:
						request.recnums.append(obj.recnum)
	
		# To avoid user filling up our system, we check that the request is reasonable
	try:
		user_disk_quota = request.user.profile.user_disk_quota
	except UserProfile.DoesNotExist:
		user_disk_quota = GlobalConfig.get("default_user_disk_quota", 1)
	
	# User disk quota is in GB
	user_disk_quota *= 1024*1024*1024
	used_quota = sum([r.estimated_size() for r in ExportDataRequest.objects.filter(user = request.user)])
	remaining_quota = user_disk_quota - used_quota
	
	if request.estimated_size() > remaining_quota:
		update_request_status(request, "TOO LARGE")
		send_message('wizard/user_request_toolarge_email_subject.txt', 'wizard/user_request_toolarge_email_content.txt', request.user, kwargs = {"request": request, "user_disk_quota": user_disk_quota, "remaining_quota":  remaining_quota}, by_mails = True, copy_to_admins = True)
	
	else:
		log.debug("Found %s records to download", len(request.recnums))
		update_request_status(request, "PROCESSING (%s/%s remaining)" % (len(request.task_ids), len(request.recnums)))
		
		# Create all the download and make_link tasks
		download_and_link_tasks = list()
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
				async_result = (get_data.s(data_download_request) | create_link.s(link_path, soft = False, force = True)).apply_async()
				# Save the task id into the request to allow monitoring and easy cancel
				request.task_ids.append(async_result.id)
		request.save()

@app.task
def curate_export_data_requests():
	log.debug("curate_export_data_requests")
	
	request_timeout = GlobalConfig.get("export_data_request_timeout", timedelta(days=1))
	for request_id in ExportDataRequest.objects.values_list('id', flat=True):
		update_export_data_request.delay(request_id, request_timeout)

@app.task
def update_export_data_request(request_id, request_timeout = GlobalConfig.get("export_data_request_timeout", timedelta(days=1))):
	log.debug("update_export_data_request %s", request_id)
	try:
		with transaction.atomic():
			request = ExportDataRequest.objects.select_for_update(nowait=True).get(id=request_id)
	except OperationalError, why:
		log.warning("Could not lock database row for ExportDataRequest %s: %s", request_id, why)
	else:
		if request.status.starts_with("PROCESSING"):
			# Sort the request tasks by status
			done_tasks, failed_tasks, pending_tasks = [], [], []
			for task_id in request.task_ids:
				task_status = app.backend.get_status(task_id)
				if task_status == "SUCCESS":
					done_tasks.append(task_id)
				elif task_status in ["PENDING", "STARTED"]:
					pending_tasks.append(task_id)
				else:
					log.error("Task %s has a status of %s", task_id, task_status)
					failed_tasks.append(task_id)
			
			# Some tasks are still pending
			if pending_tasks:
				request.task_ids = pending_tasks + failed_tasks
				# If the request is running for too long we stop it, we update the status and send an email
				if datetime.now() - request.updated > request_timeout:
					request.status = "TIMEOUT (%s/%s missing)" % (len(request.task_ids), len(request.recnums))
					request.save()
					send_message('wizard/user_request_timeout_email_subject.txt', 'wizard/user_request_timeout_email_content.txt', request.user, kwargs = {"request": request, "partial": len(request.task_ids) < len(request.recnums)}, by_mails = True, copy_to_admins = True)
				else:
					request.status = "PROCESSING (%s/%s remaining)" % (len(request.task_ids), len(request.recnums))
					request.save()
			# We only have failed tasks left, we update the status and send an email
			elif failed_tasks:
				request.task_ids = failed_tasks
				request.status = "FAILED (%s/%s missing)" % (len(request.task_ids), len(request.recnums))
				request.save()
				errors = [make_link.AsyncResult(task_id).get() for task_id in failed_tasks]
				send_message('wizard/user_request_failure_email_subject.txt', 'wizard/user_request_failure_email_content.txt', request.user, kwargs = {"request": request, "partial": len(request.task_ids) < len(request.recnums), "errors":  errors}, by_mails = True, copy_to_admins = True)
			# The tasks are all finished, we update the status and send an email
			else:
				request.task_ids = []
				request.status = "READY"
				request.save()
				send_message('wizard/user_request_success_email_subject.txt', 'wizard/user_request_success_email_content.txt', request.user, kwargs = {"request": request}, by_mails = True, copy_to_admins = True)


@app.task(bind=True)
def execute_export_metadata_request(self, request, recnums, paginator):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	
	# Save the task id into the user request to allow easy cancel
	request.task_ids = [self.request.id]
	update_request_status(request, "STARTED")
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(request.export_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Add the recnums from the paginator to the request (excluding recnums)
	if paginator is not None:
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					if obj.recnum not in recnums:
						request.recnums.append(obj.recnum)
	else:
		request.recnums = recnums
	
	log.debug("Found %s records", len(request.recnums))
	update_request_status(request, "RUNNING")
	
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
		send_message('wizard/user_request_failure_email_subject.txt', 'wizard/user_request_failure_email_content.txt', request.user, kwargs = {"request": request, "partial": False, "errors":  [why]}, by_mails = True, copy_to_admins = True)

	
	else:
		log.info("export_metadata_request %s SUCCESSFULL. Wrote file to %s ", request, request.export_path)
		request.task_ids = []
		request.status = "READY"
		request.save()
		send_message('wizard/user_request_success_email_subject.txt', 'wizard/user_request_success_email_content.txt', request.user, kwargs = {"request": request}, by_mails = True, copy_to_admins = True)

