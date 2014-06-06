#!/usr/bin/env python

from __future__ import absolute_import
import sys, os, errno
# This should go
sys.path.append('/home/benjmam/SDO')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

from celery import Celery
from celery.utils.log import get_task_logger

log = get_task_logger("test")
app = Celery('app', broker='amqp://', backend='amqp://')

# Optional configuration, see the application user guide.
app.conf.update(
	CELERY_TASK_RESULT_EXPIRES=3600,
	CELERY_TRACK_STARTED = True,
	CELERY_ACKS_LATE = True,
	CELERY_DISABLE_RATE_LIMITS = True, # To be removed if we set a rate limit on some tasks
)

from PMD.models import DataSite, DataSeries, LocalDataLocation
from PMD.request import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest
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

if __name__ == '__main__':
	app.start()
