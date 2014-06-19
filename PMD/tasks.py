#!/usr/bin/env python
from __future__ import absolute_import
import sys, os, errno
from datetime import datetime, timedelta, date

# This should go
sys.path.append('/home/benjmam/SDO')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings
from django.db import transaction

from celery import Celery
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

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
)

from PMD.models import GlobalConfig, DataSite, DataSeries, LocalDataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest
from PMD.celery_tasks.SftpDownloader import SftpDownloader
from PMD.celery_tasks.HttpDownloader import HttpDownloader
from PMD.celery_tasks.DrmsDataLocator import DrmsDataLocator
from PMD.routines.update_fits_header import update_fits_header

# TODO: if data download fails because location is incorrect allow for a get_data_location and a new essay to download the file
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
	return file_path

# Update Data - Execute a MetaDataUpdateRequest
@app.task
def update_file_meta_data(request):
	log.debug("update_file_meta_data %s", request)
	"""Locate the file, get the new header values from database and update the header of the file"""
	# Find the local file path
	file_path = get_file_path(request, local_data_site = True)
	
	# Get the new meta data
	header_values = request.data_series.get_header_values(request)
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
	log.debug("check_file_exists %s", request)
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
		data_downloader.setup(host_name = data_site.data_download_server, user_name = data_site.data_download_user, password = data_site.data_download_password, port = data_site.data_download_port, timeout = data_site.data_download_timeout)
		
		return data_downloader
	
	elif data_site.data_download_protocol == "http":
		# create a http downloader task
		@app.task(base=HttpDownloader, name=data_site.name + "_data_downloader", bind=True)
		def data_downloader(self, request):
			self.download(request.remote_file_path, request.local_file_path, log)
			return request
		
		# setup the task
		data_downloader.setup(server = data_site.data_download_server, timeout = data_site.data_download_timeout)
		
		return data_downloader
	
	else:
		raise NotImplementedError("Task not implemented for protocol type %s for data site %s" % (data_site.data_download_protocol, data_site.name))

def create_data_locator(data_site):
	"""Create specific data locator task for each data site"""
	log.debug("Creating %s data_locator for %s", data_site.data_download_protocol, data_site.name)
	
	# create a DRMS data locator task
	@app.task(base=DrmsDataLocator, name=data_site.name + "_data_locator", bind=True)
	def data_locator(self, request):
		result = self.locate(request.sunum, log)
		self.update_request(request, result, log)
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
def warn_admin(message, *args):
	"Send a message to the administrators"
	log.critical(message, *args)

@app.task
def warn_admin_callback(task_id, message = "", *args):
	"Calls warn_admin as a callback, adding the result of the calling task to the message"
	# We cannot put a "get" here contrary to the example
	# but we are sure that when come here, the task is finished
	result = AsyncResult(task_id).result
	
	if result is None:
		warn_admin(message + " No result", *args)
	elif issubclass(result, Exception):
		warn_admin(message + " Exception: %s", *(args + result))
	else:
		warn_admin(message + " Result: %s", *(args + result))

@app.task
def execute_data_download_requests():
	log.debug("execute_data_download_requests")
	
	request_timeout = GlobalConfig.get("data_download_request_timeout")
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataDownloadRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				request.status = "RUNNING"
				request.save()
				get_data.apply_async((request, ), link=update_request_status.si(request, "DONE"), link_error = warn_admin_callback.s("Data download request %s failed", request))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request_timeout is not None and datetime.now() - request.updated > request_timeout:
				warn_admin.delay("The following request %s has been running since %s and passed it's timeout %s", request, request.updated, data_download_request_timeout)
			
			elif request.status == "DONE":
				request.delete()

@app.task
def execute_data_location_requests():
	log.debug("execute_data_location_requests")
	
	request_timeout = GlobalConfig.get("data_location_request_timeout")
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataLocationRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				request.status = "RUNNING"
				request.save()
				get_data_location.apply_async((request, ), link=update_request_status.si(request, "DONE"), link_error = warn_admin_callback.s("Data location request %s failed", request))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request_timeout is not None and datetime.now() - request.updated > request_timeout:
				warn_admin.delay("The following request %s has been running since %s and passed it's timeout %s", request, request.updated, data_download_request_timeout)
			
			elif request.status == "DONE":
				request.delete()

@app.task
def execute_data_delete_requests():
	log.debug("execute_data_delete_requests")
	
	request_timeout = GlobalConfig.get("data_delete_request_timeout")
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in DataDeleteRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				request.status = "RUNNING"
				request.save()
				delete_data.apply_async((request, ), link=update_request_status.si(request, "DONE"), link_error = warn_admin_callback.s("Data delete request %s failed", request))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request_timeout is not None and datetime.now() - request.updated > request_timeout:
				warn_admin.delay("The following request %s has been running since %s and passed it's timeout %s", request, request.updated, data_download_request_timeout)
			
			elif request.status == "DONE":
				request.delete()


@app.task
def execute_meta_data_update_requests():
	log.debug("execute_meta_data_update_requests")
	
	request_timeout = GlobalConfig.get("meta_data_update_request_timeout")
	
	# Only one of these should run at any time
	# So open a transaction and lock the rows in nowait
	with transaction.atomic():
		for request in MetaDataUpdateRequest.objects.select_for_update(nowait=True).all():
			if request.status == "NEW":
				request.status = "RUNNING"
				request.save()
				update_file_meta_data(request).apply_async((request, ), link=update_request_status.si(request, "DONE"), link_error = warn_admin_callback.s("Meta-data update request %s failed", request))
			
			# If the request is running for too long there could be a problem
			elif request.status == "RUNNING" and request_timeout is not None and datetime.now() - request.updated > request_timeout:
				warn_admin.delay("The following request %s has been running since %s and passed it's timeout %s", request, request.updated, data_download_request_timeout)
			
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
	
	root_folder = GlobalConfig.get(config + "_root_folder")
	if root_folder is None:
		raise Exception("create_SDO_synoptic_tree: root_folder for %s is not configured" % config)
	
	frequency = GlobalConfig.get(config + "_frequency")
	if frequency is None:
		raise Exception("create_SDO_synoptic_tree: frequency for %s is not configured" % config)
	
	start_date = GlobalConfig.get(config + "_start_date")
	if start_date is None:
		start_date = datetime(2010, 02, 11) # SDO was launched on 11th of February 2010
		log.info("Start date not specified. Creating the SDO synoptic tree from beggining %s", start_date)
	
	soft_link = GlobalConfig.get(config + "_soft_link", False)
	
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
			link_path = os.path.join(root_folder, desc, date.strftime("%Y/%m/%d/%H"), record.filename())
			get_data.apply_async((request, ), link=create_link.s(link_path, soft=soft_link), link_error = warn_admin_callback.s("Data download request %s failed", request))
	
	# We save the start date for the next run
	start_date_config = GlobalConfig(name = config + "_start_date", value = start_date.isoformat(), python_type = "datetime", help_text = "Start date for create_SDO_synoptic_tree %s" % config)
	start_date_config.save()


if __name__ == '__main__':
	app.start()
