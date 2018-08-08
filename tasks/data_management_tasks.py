#!/usr/bin/env python
from __future__ import absolute_import
import os, errno
from datetime import datetime, timedelta

from django.db import transaction, OperationalError
from celery import group, chord
from celery.utils.log import get_task_logger

from global_config.models import GlobalConfig
from account.models import UserProfile

from PMD.models import DataSite, DataSeries, LocalDataLocation
from PMD.models import DataDownloadRequest

from tasks.routines import update_fits_header, create_png, create_record_sets
from tasks.data_locators import create_data_locator, LocationNotFound
from tasks.data_downloaders import create_data_downloader, FileNotFound

from tasks import app, check_file_exists, create_link, delete_file, update_request_status

log = get_task_logger("SDO")

data_downloaders = dict()
data_locators = dict()


# TODO add soft limit to requests http://celery.readthedocs.org/en/latest/userguide/workers.html#time-limits
# http://celery.readthedocs.org/en/latest/userguide/tasks.html#retrying

# Create Data - Execute a DataDownloadRequest
@app.task
def download_data(request):
	log.debug("download_data %s", request)
	# Get the local path where to download the file to
	request.local_file_path = LocalDataLocation.create_location(request)
	#import pdb; pdb.set_trace()
	# Create the directory tree
	try:
		os.makedirs(os.path.dirname(request.local_file_path))
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	# Try to download from each data site in order of preference until OK
	download_ok = False
	for data_site in get_prefered_datasites(request):
		request.data_site = data_site
		try:
			# Get the remote file path
			request.remote_file_path = get_data_location(request)
		except LocationNotFound, why:
			log.debug("No data location found @ %s for request %s: %s", data_site.name, request, why)
		except Exception, why:
			log.error("Error while locating data @ %s for request %s: %s", data_site.name, request, why)
		else:
			attempts = max(data_site.data_download_max_attempts, 1)
			while attempts > 0:
				attempts -= 1
				# We call the specific data site downloader
				try:
					if request.data_site.name not in data_downloaders:
						data_downloaders[request.data_site.name] = create_data_downloader(request.data_site, log)
					log.info("Downloading data @ %s for request %s", request.data_site.name, request)
					data_downloaders[request.data_site.name](request)
				# If data download fail because of wrong data location force a locate data
				except FileNotFound:
					log.info("Data not found where it was expected @ %s for request %s. Forcing a locate data request.", request.data_site.name, request)
					try:
						request.remote_file_path = locate_data(request)
					except Exception, why:
						# If locate data does not find the path (raise exception) just pass the server
						attempts = 0
				except Exception, why:
					log.error("Error while downloading data @ %s for request %s : %s. Attempts lefts: %s", request.data_site.name, request, why, attempts)
				else:
					# We have the file
					download_ok = True
					attempts = 0
		
		if download_ok:
			break
	
	if not download_ok:
		raise Exception("Could not download data for request %s" % str(request))
	else:
		attempts = max(data_site.data_download_max_attempts, 1)
		while attempts > 0:
			attempts -= 1
			try:
				update_file_metadata(request)
			except Exception, why:
				log.error("Error while updating meta-data for request %s : %s. Attempts lefts: %s", request, why, attempts)
			else:
				break
		if attempts == 0:
			raise Exception("Could not update meta-data for request %s" % str(request))

# Read Data
@app.task
def get_data(request):
	log.debug("get_data %s", request)
	# Try to get the file path for the local data site, otherwise download the data
	try:
		file_path = get_file_path(request, local_data_site = True)
		log.debug("File for request %s already in cache", request)
	except Exception:
		log.debug("Downloading file for request %s", request)
		download_data(request)
		file_path = get_file_path(request, local_data_site = True)
	else:
		# Check that the file really exists
		if not check_file_exists(file_path):
			log.debug("File for request %s in DB but not on disk, missing %s. Downloading.", request, file_path)
			download_data(request)
			file_path = get_file_path(request, local_data_site = True)
		
		# If file exists, update the expiration date (in case it is later than current one)
		elif request.expiration_date:
			LocalDataLocation.update_expiration_date(request, request.expiration_date)
	
	return file_path

# Update Data - Execute a MetadataUpdateRequest
@app.task
def update_file_metadata(request):
	log.debug("update_file_metadata %s", request)
	"""Locate the file, get the new header values from database and update the header of the file"""
	# Find the local file path
	try:
		file_path = get_file_path(request, local_data_site = True)
	except LocalDataLocation.DoesNotExist, why:
		log.error("Error while updating meta-data for request %s : %s", request, why)
	else:
		# Get the new meta data
		header_values = request.data_series.get_header_values(request.recnum)
		header_units = request.data_series.get_header_units()
		header_comments = request.data_series.get_header_comments()
		
		# Update the fits header
		update_fits_header(file_path, header_values, header_comments, header_units, hdu = request.data_series.hdu, log = log)

# Delete Data - Execute a DataDeleteRequest
@app.task
def delete_data(request):
	log.debug("delete_data %s", request)
	
	try:
		# Find the local file path
		file_path = get_file_path(request, local_data_site = True)
		# Delete the file
		delete_file(file_path)
	except LocalDataLocation.DoesNotExist:
		log.info("No file for %s", request)
	
	# Delete the data location
	LocalDataLocation.delete_location(request)

# Read Meta Data
@app.task
def get_metadata(request):
	log.debug("get_metadata %s", request)
	return request.data_series.get_header(request)

# Create Data Location - Execute a DataLocationRequest
@app.task
def locate_data(request):
#	import pdb; pdb.set_trace()
	log.debug("locate_data %s", request)
	attempts = max(request.data_site.data_location_request_max_attempts, 1)
	while attempts > 0:
		attempts -= 1
		# We call the specific data site locator
		try:
			if request.data_site.name not in data_locators:
				data_locators[request.data_site.name] = create_data_locator(request.data_site, log)
			data_locators[request.data_site.name](request)
		except LocationNotFound, why:
			log.info("No location found @ %s for request %s: %s", request.data_site.name, request, why)
			raise
		except Exception, why:
			log.error("Error while locating data @ %s for request %s: %s. Attempts lefts: %s", request.data_site.name, request, why, attempts)
			if attempts == 0:
				raise
		else:
			# We save the data location
			request.data_site.data_location.save_path(request, request.path)
			attempts = 0
	
	return request.data_site.data_location.get_file_path(request)


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
			return DataSite.objects.filter(enabled=True).order_by('-priority')

@app.task
def get_file_path(request, local_data_site = False):
	log.debug("get_file_path %s", request)
	if local_data_site:
		file_path = LocalDataLocation.get_file_path(request)
	else:
		file_path = request.data_site.data_location.get_file_path(request)
	
	return file_path

@app.task
def delete_file(file_path):
	log.debug("delete_file %s", file_path)
	try:
		os.remove(file_path)
	except OSError as why:
		if why.errno != errno.ENOENT:
			raise


@app.task
def create_AIA_HMI_synoptic_tree(config, start_date = None, end_date=None, root_folder = None, frequency = None, soft_link = None):
	""" Creates a synoptic directory tree of SDO data, takes as argument a prefix for the following Global Configuration variables:
	{prefix}_start_date: date at which to start the synoptic tree
	{prefix}_root_folder: The folder where the tree will be created
	{prefix}_frequency: The frequency of the synoptic dataset (must be of type timedelta)
	{prefix}_soft_link: Set to true if you want soft link instead of hard link
	
	These parameters can also be passed manually by name, in which case they will override the value in the Global configuration variables
	"""
	log.debug("create_SDO_synoptic_tree %s", config)
	
	# Set to True if the global config variables must be updated at the end
	update_config = False
	
	# Parse the parameters
	if start_date is None:
		start_date = GlobalConfig.get(config + "_start_date", datetime(2010, 03, 29))
		update_config = True
	
	if end_date is None:
		end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
	
	if root_folder is None:
		root_folder = GlobalConfig.get_or_fail(config + "_root_folder")
	
	if frequency is None:
		frequency = GlobalConfig.get_or_fail(config + "_frequency")
	
	if soft_link is None:
		soft_link = GlobalConfig.get(config + "_soft_link", False)
	
	# Create the dataseries descriptions
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
	log.debug("Getting records from %s to %s", start_date, end_date)
	record_sets = create_record_sets(data_series_desc, frequency, start_date, end_date)
	
	# Remove the last record sets that are incomplete
	times = sorted(record_sets.keys())
	while times and len(record_sets[times[-1]]) < len(data_series_desc):
		log.debug("Record set for time %s is incomplete %s/%s, delaying until next run.", times[-1].isoformat(), len(record_sets[times[-1]]), len(data_series_desc))
		del record_sets[times[-1]]
		times.pop()
	
	# We get the files and make the links
	for time, record_set in record_sets.iteritems():
		log.debug("Requesting data and creating links for %s", time.isoformat())
		for desc, record in record_set.iteritems():
			request = DataDownloadRequest.create_from_record(record)
			link_path = os.path.join(root_folder, desc, time.strftime("%Y/%m/%d"), record.filename)
			get_data.apply_async((request, ), link=create_link.s(link_path, soft=soft_link, force=True), link_error=update_request_status.si(request, "FAILED"))
		
	# We save the start date for the next run if any record set was processed
	if update_config and record_sets:
		start_date = max(record_sets.iterkeys())
		log.info("Next start date will be %s", start_date)
		GlobalConfig.set(config + "_start_date", start_date, help_text = "Start date for create_SDO_synoptic_tree %s" % config)


# Django tasks
@app.task
def get_preview(request):
	# Check if the previews already exists
	cache_path = GlobalConfig.get_or_fail("preview_cache_path")
	image_path = os.path.splitext(os.path.join(cache_path, request.data_series.name, "%s.%s" % (request.recnum, request.segment)))[0] + ".png"
	if os.path.exists(image_path):
		return image_path
	
	# Get the fits file
	fits_path = get_data(request)
	
	# Create the preview
	fits2png = GlobalConfig.get("fits2png_path", "fits2png.x")
	create_png(fits_path, image_path, {"upperLabel" : "", "color": "true", "size": "512x512"}, fits2png)
	
	return image_path


@app.task
def sanitize_local_data_location():
	log.debug("sanitize_local_data_location")
	# import pdb; pdb.set_trace()
	# We check that the data_cache_path is not empty
	# otherwise the nfs could be not mounted and it would result in all files being deleted
	cache_path = GlobalConfig.get_or_fail("data_cache_path")
	if not os.path.exists(cache_path) or not os.listdir(cache_path):
		raise Exception("Cancelling sanitize_local_data_location, suspecting nfs storage not mounted: %s is empty" % cache_path)
	
	data_location_ids = LocalDataLocation.objects.values_list("id", flat=True)
	# Check for each local data location registered if that the files exists
	# Rows are locked one by one to minimize service interruption
	for data_location_id in data_location_ids:
		try:
			with transaction.atomic():
				try:
					data_location = LocalDataLocation.objects.select_for_update(nowait=True).get(id=data_location_id)
				except LocalDataLocation.DoesNotExist:
					pass
				else:
					if not check_file_exists(data_location.path):
						log.info("Cleaning up LocalDataLocation, missing file for %s", data_location)
						data_location.delete()
		except OperationalError, why:
			log.warning("Could not lock database rows for LocalDataLocation: %s", why)
	
	
	# Check that total cache usage is below limit
	# Cleanup if necessary
	
	# Check that total export cache is below limit
	# Cleanup if necessary
