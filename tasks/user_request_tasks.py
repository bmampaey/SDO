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

from tasks import app, create_link, get_data, send_email, update_request_status

log = get_task_logger("SDO")

# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# TODO send mail when too big
@app.task(bind=True)
def execute_export_data_request(self, request, recnums, paginator):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	#from celery.contrib import rdb; rdb.set_trace()
	
	# Save the task id into the user request to allow easy cancel
	request.task_ids = [self.request.id]
	update_request_status(request, "STARTED")
	
	# Create the directory tree
	try:
		os.makedirs(request.export_path)
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# To avoid user filling up our system, we check that the request is reasonable
	try:
		user_disk_quota = request.user.profile.user_disk_quota
	except UserProfile.DoesNotExist:
		user_disk_quota = GlobalConfig.get("default_user_disk_quota", 1)
	
	# User disk quota is in GB
	user_disk_quota *= 1024*1024*1024
	used_quota = sum([r.estimated_size() for r in ExportDataRequest.objects.filter(user = request.user)])
	remaining_quota = user_disk_quota - used_quota
	
	if remaining_quota <= 0:
		raise Exception("User %s has no disk quota left for request %s" % (request.user, request))
	
	# Add the recnums from the paginator to the request (excluding recnums)
	if paginator is not None:
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
				if request.estimated_size() > remaining_quota:
					update_request_status(request, "NO DISK LEFT")
					raise Exception("User request %s %s is larger than maximum allowed size" % (request.type, request.id)) 
	
	else:
		request.recnums = recnums
		if request.estimated_size() > remaining_quota:
			update_request_status(request, "NO DISK LEFT")
			raise Exception("User request %s %s is larger than maximum allowed size" % (request.type, request.id)) 
	
	log.debug("Found %s records to download", len(request.recnums))
	update_request_status(request, "RUNNING")
	
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
			download_and_link_tasks.append(get_data.s(data_download_request) | create_link.s(link_path, soft = False, force = True))
	
	#import pdb; pdb.set_trace()
	# Execute all the link tasks in parralel, then mark status as done and send email
	download_and_link_tasks_chord = chord(download_and_link_tasks, post_execute_export_data_request.s(request))
	
	# Start the task
	async_result = download_and_link_tasks_chord.delay()
	
	# Save the task id into the request to allow easy cancel
	# async_result.save_group() # Not yet implemented See http://celery.readthedocs.org/en/latest/reference/celery.result.html#celery.result.GroupResult
	# Once it is implemented it can be used to revoque requests (see views) and get error status
	request.task_ids.append(async_result.id)
	request.task_ids.extend([child.id for child in async_result.parent.children])
	request.save()

@app.task
def post_execute_export_data_request(results, request):
	log.debug("post_execute_export_data_request results %s request %s", results, request)
	
	# Check if there was any error
	errors = ""
	for result in results:
		if isinstance(result, Exception):
			errors.append(str(result))
	
	if errors:
		log.error("export_data_request %s FAILED: %s", request, str(errors))
		update_request_status(request, "FAILED")
		mail_content = render_to_string('wizard/user_request_failure_email_content.txt', {'request': request, 'errors': errors, 'partial' : len(errors) < len(results[0])})
		mail_subject = render_to_string('wizard/user_request_failure_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = True)
	
	else:
		log.info("export_data_request %s SUCCESSFULL. Wrote files to %s ", request, request.export_path)
		update_request_status(request, "DONE")
		mail_content = render_to_string('wizard/user_request_success_email_content.txt', {'request': request})
		mail_subject = render_to_string('wizard/user_request_success_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = False)


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
		# send mail to user
		mail_content = render_to_string('wizard/user_request_failure_email_content.txt', {'request': request})
		mail_subject = render_to_string('wizard/user_request_failure_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = True)
	
	else:
		log.info("export_metadata_request %s SUCCESSFULL. Wrote files to %s ", request, request.export_path)
		update_request_status(request, "DONE")
		# send mail to user
		mail_content = render_to_string('wizard/user_request_success_email_content.txt', {'request': request})
		mail_subject = render_to_string('wizard/user_request_success_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email)
