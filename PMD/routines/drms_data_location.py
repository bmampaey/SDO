#!/usr/bin/python
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

def break_url(url):
	"""Break a URL in server and path""" 
	url_parts = urlparse.urlparse(url)
	
	if url_parts.scheme != "http" and url_parts.scheme != "":
		raise Exception("URL scheme is not http. URL was %s" % url)
	
	elif not url_parts.netloc:
		raise Exception("URL netloc not specified. URL was %s" % url)
	
	return url_parts.netloc, url_parts.path

def get_http_client(server, timeout = 120):
	'''Create and return an http connection to a host'''
	return httplib.HTTPConnection(server, timeout = timeout)

# According to Igor, it is possible that the jsoc_fetc cgi will fail for some sunums, or if the number of sunums passed is too big
# In the JMD the solution is to shuffle them and to limit the query to max 100 sunums
# Another possible solution would be to divide a failing request into 2 smaller requests
# But let's see first if this is a real problem
def call_jsoc_fetch(http_client, url, sunums, method = "GET", log = None):
	'''Query a drms data site for the location of sunums'''
	results = dict()
	if len(sunums) > 0:
		# We create the query for the http request
		sunums = [str(sunum) for sunum in sunums]
		url  += "?op=exp_su&method=url_quick&format=json&formatvar=dataobj&protocol=as-is&requestid=NOASYNCREQUEST&sunum={sunums}".format(sunums=",".join(sunums))
		
		# We try to get the http response
		if log is not None:
			log.debug("Making request for URL %s", url)
		http_client.request(method, url)
		response = http_client.getresponse()
		response_content = response.read()
		if log is not None:
			log.debug("Received response content %s", response_content)
		
		# We parse the response to json
		response_json = json.loads(response_content)
		data = response_json["data"]
		
		# We associate the result with the sunum
		for sunum in sunums:
			if sunum in data:
				results[int(sunum)] = data[sunum]
			else:
				if log is not None:
					log.warning("Requested sunum %s not in response data: %s", sunum, data)
				results[int(sunum)] = dict()
	
	return results


def update_request(request, result, log = None):
	'''Update a data location request with the result of a call_jsoc_fetch'''
	
	if 'path' not in result or result['path'].upper() == "NA":
		raise Exception("No path found in result %s for request %s" % (result, request))
	
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
	
	elif request.data_series.data_series.name is not None and result['series'] != request.data_series.data_series.name:
		# Because we don't know how to cope we just throw an exception
		raise Exception("Mismatch series name in result %s for request %s" % (result, request))
	
	else:
		if log is not None:
			log.debug("Found path %s for sunum %s with size %s", result['path'], request.sunum, result['susize'])
		request.path = result['path']
		request.size = int(result['susize'])

