#!/usr/bin/python
import logging
import json
import signal
import threading
import Queue
import httplib
import urlparse
import os
import sys
import time
from django.db import IntegrityError
from get_config import get_config, update_config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

sys.path.append('/home/benjmam/SDO')
from PMD.models import DataSite, DataSeries

# According to Igor, it is possible that the jsoc_fetc cgi will fail for some sunums, or if the number of sunums passed is too big
# In the JMD the solution is to shuffle them and to limit the query to max 100 sunums
# Another possible solution would be to divide a failing request into 2 smaller requests
# But let's see first if this is a real problem
def get_drms_data_location(data_location_query_url, sunums, timeout = 120, max_attempts = 3, method = "GET", log = logging):
	'''Query a drms data site for the location of sunums'''
	
	# httplib need the URL to be broken down into a scheme, a hostname and a path
	log.debug("Querying data location with parameters: %s", method)
	url_parts = urlparse.urlparse(data_location_query_url)
	if url_parts.scheme != "http" and url_parts.scheme != "":
		raise Exception("URL scheme is not http. URL was %s" % data_location_query_url)
	elif not url_parts.netloc:
		raise Exception("URL netloc not specified. URL was %s" % data_location_query_url)
	
	result = dict()
	if len(sunums) > 0:
		# We create the query for the http request
		sunums = [str(sunum) for sunum in sunums]
		sunums_query = "?op=exp_su&method=url_quick&format=json&formatvar=dataobj&protocol=as-is&requestid=NOASYNCREQUEST&sunum={sunums}".format(sunums=",".join(sunums))
		
		# We allow several attemps to get the response
		remaining_attempts = max_attempts
		response_content = None
		while remaining_attempts > 0 and response_content is None:
			try:
				# We try to get the http response
				connection = httplib.HTTPConnection(url_parts.netloc, timeout = timeout)
				logging.debug("Retrieving URL %s", url_parts.path + sunums_query)
				connection.request(method, url_parts.path + sunums_query)
				response = connection.getresponse()
				if response.status != httplib.OK:
					raise Exception(response.reason)
				else:
					response_content = response.read()
			except Exception, why:
				# Something went wrong, we lost an attempt
				remaining_attempts -= 1
				log.warning("Failed attempt %s/%s retrieving URL %s: %s.", max_attempts-remaining_attempts, max_attempts, data_location_query_url + sunums_query, str(why))
			finally:
				connection.close()
		
		if remaining_attempts == 0 or response_content is None: # We failed getting a response from the server
			raise Exception("Could not retrieve URL %s, %s failures. Last failure was %s." % (data_location_query_url + sunums_query, max_attempts, str(why)))
		
		else: # Success! We parse the response content to json and extract the important stuff
			try:
				response_json = json.loads(response_content)
			except Exception, why:
				raise Exception("Error parsing json from response to URL %s: %s. Response was: %s" % (data_location_query_url + sunums_query, str(why), response_content))
			
			if not "data" in response_json: # The response is not what we expected
				raise Exception("No data member available in response to URL %s. Response was: %s" % (data_location_query_url + sunums_query, response_content))
			
			data = response_json["data"]
			for sunum in sunums:
				if sunum in data:
					log.debug("Found sunum %s in response: %s", sunum, data[sunum])
					result[int(sunum)] = data[sunum]
				else:
					log.warning("Requested sunum %s not in response data: %s", sunum, data)
					result[int(sunum)] = None
	
	return result


def update_request(request, result, log = logging):
	'''Update a data location request with a data location result'''
	
	if 'path' not in result or result['path'].upper() == "NA":
		raise Exception("No path found in result %s for request %s" % (result, request))
	
	# Do we need the size ?
	elif 'susize' not in result:
		# Because we don't know how to cope we just throw an exception
		raise Exception("No susize found in result %s for request %s" % (result, request))
	
	# Do we need those additional checks ?
	elif 'sustatus' not in result:
		# Because we don't know how to cope we just throw an exception
		raise Exception("No sustatus found in result %s for request %s" % (result, request))
		
	elif result['sustatus'].upper() != "Y":
		# Because we don't know how to cope we just throw an exception
		raise Exception("Status different than Y in result %s for request %s" % (result, request))
	
	elif 'sunum' not in result:
		# Because we don't know how to cope we just throw an exception
		raise Exception("No sunum found in result %s for request %s" % (result, request))
	
	elif result['sunum'] != str(request.sunum):
		# Because we don't know how to cope we just throw an exception
		raise Exception("Mismatch sunum in result %s for request %s" % (result, request))
	
	elif 'series' not in result:
		# Because we don't know how to cope we just throw an exception
		raise Exception("No series found in result %s for request %s" % (result, request))
	
	elif request.data_series_name is not None and result['series'] != request.data_series_name:
		# Because we don't know how to cope we just throw an exception
		raise Exception("Mismatch series name in result %s for request %s" % (result, request))
	
	else:
		log.debug("Found path %s for sunum %s with size %s", result['path'], request.sunum)
		request.path = result['path']
		request.size = int(result['susize'])


def save_drms_data_location(data_location_model, request, log = logging):
	'''Save the path of a drms data location request to DB'''
	
	# The data location model takes a data_series instance and not just the name
	# If the data series does not exists it should throw a DoesNotExist Exception
	data_series = DataSeries.objects.get(pk = request.data_series_name)
	
	# We first assume that the path was no already in the data location table, and we create a new one
	data_location = data_location_model(data_series = data_series, sunum = request.sunum, recnum = request.recnum, path = request.path)
	log.debug("Saving path %s for sunum %s to data location table of %s", request.path, request.sunum, request.data_site_name)
	try:
		data_location.save()
	except IntegrityError, why:
		# The path was already in the data location table, so we update with the new path
		log.debug("Path for request %s was already in table, try to update instead", request)
		data_location = data_location_model.objects.get(sunum = request.sunum)
		if data_location.data_series.name != data_series.name:
			raise Exception("Data series %s for sunum %s is not coherent with previously known data series %s. Not updating!" % (data_series.name, request.sunum, data_location.data_series.name))
		else:
			data_location.path = request.path
			data_location.save()
	
	return request
	
