#!/usr/bin/env python
from __future__ import absolute_import
import sys, os, errno, socket
from datetime import datetime, timedelta, date

# This should go
sys.path.append('/home/benjmam/SDO')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings
from django.db import transaction
from django.core import mail
from django.template.loader import render_to_string

from celery import Celery, group, chord
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

import csv

log = get_task_logger("test")
app = Celery('app', broker='amqp://', backend='amqp://')


celery_beat_schedule = {
	'execute_data_download_requests': {
		'task': 'PMD.tasks.execute_data_download_requests',
		'schedule': timedelta(seconds=20),
		'args': ()
	},
}

# Optional configuration, see the application user guide.

app.conf.update(
	CELERY_TASK_RESULT_EXPIRES=3600,
	CELERY_TRACK_STARTED = True,
	CELERY_ACKS_LATE = True,
	CELERY_DISABLE_RATE_LIMITS = True, # To be removed if we set a rate limit on some tasks
	CELERY_TIMEZONE = 'Europe/Brussels',
	CELERYBEAT_SCHEDULE = celery_beat_schedule,
	# Send a mail each time a task fail
	CELERY_SEND_TASK_ERROR_EMAILS = True,
	# Emails settings are overriden by Django email settings.
	ADMINS = settings.ADMINS,
	SERVER_EMAIL = settings.DEFAULT_FROM_EMAIL,
	EMAIL_HOST = settings.EMAIL_HOST,
)

from PMD.models import GlobalConfig, DataSite, DataSeries, LocalDataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest
from PMD.celery_tasks.SftpDownloader import SftpDownloader
from PMD.celery_tasks.HttpDownloader import HttpDownloader
from PMD.celery_tasks.DrmsDataLocator import DrmsDataLocator
from PMD.celery_tasks.Exceptions import FileNotFound
from PMD.routines.update_fits_header import update_fits_header
from PMD.routines.create_png import create_png

# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# http://celery.readthedocs.org/en/latest/userguide/tasks.html#retrying

# Create Data - Execute a DataDownloadRequest
@app.task
def download_data(request):
	log.debug("download_data %s", request)
	# Get the local path where to download the file to
	request.local_file_path = LocalDataLocation.create_location(request)
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(request.local_file_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Try to download from each data site in order of preference until OK
	for data_site in get_prefered_datasites(request):
		request.data_site = data_site
		try:
			# Get the remote file path
			request.remote_file_path = get_data_location(request)
		except Exception, why:
			log.debug("No data location found for request %s: %s", request, why)
		else:
			# We call the specific data site downloader
			try:
				data_downloaders[request.data_site.name](request)
			# If data download fail because of wrong data location retry
			except FileNotFound:
				request.remote_file_path = locate_data(request)
				data_downloaders[request.data_site.name](request)
			break
			
	
	update_file_meta_data(request)

# Read Data
@app.task
def get_data(request):
	log.debug("get_data %s", request)
	# Try to get the file path for the local data site, otherwise download the data
	try:
		file_path = get_file_path(request, local_data_site = True)
	except Exception:
		download_data(request)
		file_path = get_file_path(request, local_data_site = True)
	else:
		# Check that the file really exists
		if not check_file_exists(file_path):
			download_data(request)
			file_path = get_file_path(request, local_data_site = True)
		
		# If file exists, update the expiration date (in case it is later than current one)
		elif request.expiration_date:
			LocalDataLocation.update_expiration_date(request, request.expiration_date)
	
	return file_path

# Update Data - Execute a MetaDataUpdateRequest
@app.task
def update_file_meta_data(request):
	log.debug("update_file_meta_data %s", request)
	"""Locate the file, get the new header values from database and update the header of the file"""
	# Find the local file path
	file_path = get_file_path(request, local_data_site = True)
	
	# Get the new meta data
	header_values = request.data_series.get_header_values(request.recnum)
	header_units = request.data_series.get_header_units()
	header_comments = request.data_series.get_header_comments()
	
	# Update the fits header
	update_fits_header(file_path, header_values, header_comments, header_units, request.data_series.hdu, log)

# Delete Data - Execute a DataDeleteRequest
@app.task
def delete_data(request):
	log.debug("delete_data %s", request)

	# Find the local file path
	file_path = get_file_path(request, local_data_site = True)
	
	# Delete the file
	delete_file(file_path)
	
	# Delete the data location
	LocalDataLocation.delete_location(request)

# Read Meta Data
@app.task
def get_meta_data(request):
	log.debug("get_meta_data %s", request)
	return request.data_series.get_header(request)

# Create Data Location - Execute a DataLocationRequest
@app.task
def locate_data(request):
	log.debug("locate_data %s", request)
	# We call the specific data site locator
	data_locators[request.data_site.name](request)
	
	# We save the data location
	request.data_site.data_location.save_path(request, request.path)
	
	return data_site.data_location.get_file_path(request)


# Read Data Location
@app.task
def get_data_location(request):
	log.debug("get_data_location %s", request)
	# Try to get the file path from the database, otherwise do a locate_data to find it
	try:
		file_path = get_file_path(request)
	except Exception, why:
		file_path = locate_data(request)
	
	return file_path

# Update Data Location
@app.task
def update_data_location(request):
	log.debug("update_data_location %s", request)
	raise NotImplementedError("update_data_location was not implemented")

# Delete Data Location
@app.task
def delete_data_location(request):
	log.debug("delete_data_location %s", request)
	request.data_site.data_location.delete_location(request)

# Routines
def get_prefered_datasites(request):
	log.debug("get_prefered_datasites %s", request)
	try:
		return [request.data_site]
	except DataSite.DoesNotExist:
		if request.data_series.forced_datasite:
			return [request.data_series.forced_datasite]
		else:
			return DataSite.objects.order_by('-priority')

@app.task
def get_file_path(request, local_data_site = False):
	log.debug("get_file_path %s", request)
	if local_data_site:
		file_path = LocalDataLocation.get_file_path(request)
	else:
		file_path = request.data_site.data_location.get_file_path(request)
	
	return file_path

def delete_file(file_path):
	log.debug("delete_file %s", file_path)
	try:
		os.remove(file_path)
	except OSError as why:
		if why.errno != errno.ENOENT:
			raise

def check_file_exists(file_path):
	log.debug("check_file_exists %s", file_path)
	return os.path.exists(file_path)

def get_hard_link_count(file_path):
	return os.stat(file_path).st_nlink



def create_data_downloader(data_site):
	"""Create specific data downloader task for each data site"""
	log.debug("Creating %s data_downloader for %s", data_site.data_download_protocol, data_site.name)
	
	if data_site.data_download_protocol == "sftp":
		# create a sftp downloader task
		@app.task(base=SftpDownloader, name=data_site.name + "_data_downloader", bind=True)
		def data_downloader(self, request):
			self.download(request.remote_file_path, request.local_file_path, log)
			return request
		
		# setup the task
		data_downloader.setup(server_address = data_site.data_download_server, user_name = data_site.data_download_user, password = data_site.data_download_password, server_port = data_site.data_download_port, timeout = data_site.data_download_timeout)
		
		return data_downloader
	
	elif data_site.data_download_protocol == "http":
		# create a http downloader task
		@app.task(base=HttpDownloader, name=data_site.name + "_data_downloader", bind=True)
		def data_downloader(self, request):
			self.download(request.remote_file_path, request.local_file_path, log)
			return request
		
		# setup the task
		data_downloader.setup(server_address = data_site.data_download_server, server_port = data_site.data_download_port, timeout = data_site.data_download_timeout)
		
		return data_downloader
	
	else:
		raise NotImplementedError("Task not implemented for protocol type %s for data site %s" % (data_site.data_download_protocol, data_site.name))

def create_data_locator(data_site):
	"""Create specific data locator task for each data site"""
	log.debug("Creating %s data_locator for %s", data_site.data_download_protocol, data_site.name)
	
	# create a DRMS data locator task
	@app.task(base=DrmsDataLocator, name=data_site.name + "_data_locator", bind=True)
	def data_locator(self, request):
		results = self.locate(request.sunum, log)
		self.update_request(request, results[request.sunum], log)
		return request
	
	# setup the task
	data_locator.setup(url = data_site.data_location_request_url, timeout = data_site.data_location_request_timeout)
	
	return data_locator

data_downloaders = dict()
data_locators = dict()
for data_site in DataSite.objects.all():
	data_downloaders[data_site.name] = create_data_downloader(data_site)
	data_locators[data_site.name] = create_data_locator(data_site)


@app.task
def update_request_status(request, status):
	log.debug("update_request_status %s, %s", request, status)
	
	request.status = status
	request.save()

@app.task
def execute_data_download_requests():
	log.debug("execute_data_download_requests")
	
	request_timeout = GlobalConfig.get("data_download_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataDownloadRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				update_request_status(request, "RUNNING")
				get_data.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
				update_request_status(request, "TIMEOUT")
				app.mail_admins("Request timeout", "The following request %s has been running since %s and passed it's timeout %s", request, request.updated, request_timeout)
			
			elif request.status == "DONE":
				request.delete()

@app.task
def execute_data_location_requests():
	log.debug("execute_data_location_requests")
	
	request_timeout = GlobalConfig.get("data_location_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataLocationRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				update_request_status(request, "RUNNING")
				get_data_location.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
				update_request_status(request, "TIMEOUT")
				app.mail_admins("Request timeout", "The following request %s has been running since %s and passed it's timeout %s", request, request.updated, request_timeout)
			
			elif request.status == "DONE":
				request.delete()

@app.task
def execute_data_delete_requests():
	log.debug("execute_data_delete_requests")
	
	request_timeout = GlobalConfig.get("data_delete_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataDeleteRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				update_request_status(request, "RUNNING")
				delete_data.apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
				update_request_status(request, "TIMEOUT")
				app.mail_admins("Request timeout", "The following request %s has been running since %s and passed it's timeout %s", request, request.updated, request_timeout)
			
			elif request.status == "DONE":
				request.delete()


@app.task
def execute_meta_data_update_requests():
	log.debug("execute_meta_data_update_requests")
	
	request_timeout = GlobalConfig.get("meta_data_update_request_timeout", timedelta(days=1))
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in MetaDataUpdateRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				update_request_status(request, "RUNNING")
				update_file_meta_data(request).apply_async((request, ), link=update_request_status.si(request, "DONE"))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request.updated + request_timeout < datetime.now():
				update_request_status(request, "TIMEOUT")
				app.mail_admins("Request timeout", "The following request %s has been running since %s and passed it's timeout %s", request, request.updated, request_timeout)
			
			elif request.status == "DONE":
				request.delete()

@app.task
def create_link(file_path, link_path, soft = False):
	log.debug("create_link %s -> %s", link_path, file_path)
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(link_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Make the link
	if soft:
		os.symlink(file_path, link_path)
	else:
		os.link(file_path, link_path)


@app.task
def create_SDO_synoptic_tree(config):
	""" Creates a synoptic directory tree of SDO data, takes as argument a prefix for the following Global Configuration variables:
	{prefix}_root_folder: The folder where the tree will be created
	{prefix}_frequency: The frequency of the synoptic dataset (must be of type timedelta)
	{prefix}_soft_link: Set to true if you want soft link instead of hard link
	"""
	log.debug("create_SDO_synoptic_tree %s", config)
	
	root_folder = GlobalConfig.get_or_fail(config + "_root_folder")
	frequency = GlobalConfig.get_or_fail(config + "_frequency")	
	soft_link = GlobalConfig.get(config + "_soft_link", False)
	start_date = GlobalConfig.get(config + "_start_date", datetime(2010, 02, 11))
	if start_date  <= datetime(2010, 02, 11):
		log.info("Creating the SDO synoptic tree from beggining %s", start_date)
	
	data_series_desc = dict()
	
	# For aia.lev1 it is 1 per wavelength
	aia_lev1 = DataSeries.objects.get(drms_series__name="aia.lev1")
	for wavelength in [94, 131, 171, 193, 211, 304, 335, 1600, 1700, 4500]:
		data_series_desc["aia.lev1/%04d" % wavelength] =  aia_lev1.record.objects.filter(wavelnth = wavelength, quality = 0)
	
	# We add hmi m45s and ic45s
	hmi_m_45s = DataSeries.objects.get(drms_series__name="hmi.m_45s")
	data_series_desc["hmi.m_45s"] = hmi_m_45s.record.objects.filter(quality = 0)
	hmi_ic_45s = DataSeries.objects.get(drms_series__name="hmi.ic_45s")
	data_series_desc["hmi.ic_45s"] = hmi_ic_45s.record.objects.filter(quality = 0)
	
	# Get the record sets
	record_sets = create_record_sets(data_series_desc, frequency, start_date, date.today())
	
	# We remove all the sets at the end that are not full, and set the start_date for the next run as the last not full set
	dates = record_sets.values()
	dates.sort()
	while dates and len(record_sets[dates[-1]]) < len(data_series_desc):
		start_date = dates.pop()
	
	# We get the files and make the links
	for date in dates:
		for desc, record in record_sets[date].iteritems():
			request = DataDownloadRequest.create_from_record(record)
			link_path = os.path.join(root_folder, desc, date.strftime("%Y/%m/%d/%H"), record.filename)
			get_data.apply_async((request, ), link=create_link.s(link_path, soft=soft_link))
	
	# We save the start date for the next run
	start_date_config = GlobalConfig(name = config + "_start_date", value = start_date.isoformat(), python_type = "datetime", help_text = "Start date for create_SDO_synoptic_tree %s" % config)
	start_date_config.save()

# Django tasks
@app.task
def get_preview(request):
	# Check if the previews already exists 
	cache = GlobalConfig.get_or_fail("preview_cache")
	image_path = os.path.splitext(os.path.join(cache, request.data_series.name, "%s.%s" % (request.recnum, request.segment)))[0] + ".png"
	if os.path.exists(image_path):
		return image_path
	
	# Get the fits file
	fits_path = get_data(request)
	
	# Create the preview
	fits2png = GlobalConfig.get("fits2png_path", "fits2png.x")
	create_png(fits_path, image_path, {"upperLabel" : "", "color": "true", "size": "512x512"}, fits2png)
	
	return image_path

# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# TODO send mail when too big
@app.task
def execute_export_data_request(request, paginator):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	#import pdb; pdb.set_trace()
	
	# To avoid user filling up our system, we check that the request is reasonable
	max_export_data_request_size =  GlobalConfig.get("max_export_data_request_size", 100 * 1024 * 1024 * 1024)
	if request.estimated_size() > max_export_data_request_size:
		update_request_status(request, "TOO BIG")
		raise Exception("User request %s is larger than maximum allowed size") 
	
	# Add the recnums from the paginator to the request
	if paginator is not None:
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					request.recnums.append(obj.recnum)
				if request.estimated_size() > max_export_data_request_size:
					update_request_status(request, "TOO BIG")
					raise Exception("User request %s is larger than maximum allowed size") 
	
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
			download_and_link_tasks.append(get_data.s(data_download_request) | create_link.s(link_path, soft = False))
	
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
		update_request_status(request, "FAILED")
		mail_content = render_to_string('PMD/user_request_failure_email_content.txt', {'request': request, 'errors': errors, 'partial' : len(errors) < len(results[0])})
		mail_subject = render_to_string('PMD/user_request_failure_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = True)
	else:
		update_request_status(request, "DONE")
		mail_content = render_to_string('PMD/user_request_success_email_content.txt', {'request': request})
		mail_subject = render_to_string('PMD/user_request_success_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = False)


@app.task()
def send_email(subject, content, to, copy_to_admins = False):
	log.debug("send_email %s, %s, %s", subject, content, to)
	if not isinstance(to, (list, tuple)):
		to = [to]
	
	if copy_to_admins:
		to = list(to)
		for admin in settings.ADMINS:
			to.append(admin[1])
	
	mail.send_mail(subject.replace("\n", ""), content, None, to)

@app.task
def execute_export_meta_data_request(request, paginator):
	log.debug("execute_export_data_request request %s paginator %s", request, paginator)
	
	# Add the recnums from the paginator to the request
	if paginator is not None:
		for page_number in paginator.page_range:
			try:
				page = paginator.page(page_number)
			except EmptyPage:
				pass
			else:
				for obj in page.object_list:
					request.recnums.append(obj.recnum)
	
	log.debug("Found %s records", len(request.recnums))
	update_request_status(request, "RUNNING")
	
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(request.export_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
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
		log.error("Could not write csv file %s: %s", request.export_path, why)
		update_request_status(request, "FAILED")
		# send mail to user
		mail_content = render_to_string('PMD/user_request_failure_email_content.txt', {'request': request})
		mail_subject = render_to_string('PMD/user_request_failure_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email, copy_to_admins = True)
	else:
		log.info("Succesfully wrote csv file for request %s to %s ", request, request.export_path)
		update_request_status(request, "DONE")
		# send mail to user
		mail_content = render_to_string('PMD/user_request_success_email_content.txt', {'request': request})
		mail_subject = render_to_string('PMD/user_request_success_email_subject.txt', {'request': request})
		send_email(mail_subject, mail_content, request.user.email)


if __name__ == '__main__':
	app.start()
