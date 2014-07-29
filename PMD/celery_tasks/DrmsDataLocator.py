import json
import httplib
import time
import socket
import urlparse
from celery import Task

from Exceptions import LocateError, ConnectionError, SetupError, UpdateError

class DrmsDataLocator(Task):
	abstract = True
	
	def setup(self, url, timeout = 120, method = "GET"):
		url_parts = urlparse.urlparse(url)
		
		if url_parts.scheme != "http" and url_parts.scheme != "":
			raise SetupError("URL scheme is not http. URL was %s" % url)
		
		elif not url_parts.netloc:
			raise SetupError("URL netloc not specified. URL was %s" % url)
		
		self.server_address = url_parts.hostname
		self.server_port = url_parts.port
		self.path = url_parts.path
		self.timeout = timeout
		self.method = method
		self.connection = None
	
	def open_connection(self, log = None):
		"""Open a http connection to the server"""
		if self.connection is None:
			if log is not None:
				log.info("Opening http connection to %s", self.server_address)
			
			try:
				self.connection = httplib.HTTPConnection(self.server_address, self.server_port, timeout = self.timeout)
				self.connection.connect()
			except Exception, why:
				self.connection = None
				if log is not None:
					log.error("Error while opening connection to server %s: %s", self.server_address, why)
				raise ConnectionError("Could not open connection to server %s: %s." % (self.server_address, why))
		
		return self.connection
	
	def close_connection(self, log = None):
		"""Close the http connection to the server"""
		if self.connection is not None:
			if log is not None:
				log.info("Closing http connection to %s", self.connection.host)
			self.connection.close()
			self.connection = None
	
	def locate(self, sunums, log = None):
		'''Query a drms data site for the location of sunums'''
		if log is not None:
			log.debug("Locating sunums %s from %s", sunums, self.server_address)
			start = time.time()
		
		# Parse the args
		try:
			sunums = [str(sunum) for sunum in sunums]
		except TypeError:
			sunums = [str(sunums)]
		
		results = dict()
		if len(sunums) == 0:
			return results
		
		# Open the connection
		connection = self.open_connection(log = log)
		
		url  = self.path + "?op=exp_su&method=url_quick&format=json&formatvar=dataobj&protocol=as-is&requestid=NOASYNCREQUEST&sunum={sunums}".format(sunums=",".join(sunums))
		
		# Make the request
		try:
			connection.request(self.method, url)
			response = connection.getresponse()
			response_content = response.read()
		except socket.timeout, why:
			if log is not None:
				log.error("Timeout while locating sunums %s from server %s: %s", sunums, connection.host, why)
			
			raise LocateError("Timeout while locating sunums %s from server %s: %s" % (sunums, connection.host, why))
		
		except Exception, why:
			if log is not None:
				log.error("Error while locating sunums %s from server %s: %s", sunums, connection.host, why)
			
			# Close the connection for the future requests
			self.close_connection()
			
			raise LocateError("Error while locating sunums %s from server %s: %s" % (sunums, connection.host, why))
			
		if response.status != 200:
			raise LocateError("Could not locate sunums %s from server %s. Status: %s. Reason: %s." % (sunums, connection.host, response.status, response.reason))
			
		elif log is not None:
			log.debug("Locate of sunums %s from %s took %s seconds. Response: %s.", sunums, connection.host, time.time() - start, response_content)
		
		# We parse the response to json
		try:
			response_json = json.loads(response_content)
			data = response_json["data"]
		except Exception, why:
			if log is not None:
				log.error("Error while decoding response content %s: %s", response_content, why)
			raise LocateError("Error while decoding response content %s: %s" % (response_content, why))
		
		# We associate the result with the sunum
		for sunum in sunums:
			if sunum in data:
				results[int(sunum)] = data[sunum]
			else:
				if log is not None:
					log.warning("Requested sunum %s not in response data: %s", sunum, data)
				results[int(sunum)] = dict()
		
		return results
		
	def update_request(self, request, result, log = None):
		'''Update a data location request with the result of a call_jsoc_fetch'''
		
		if 'path' not in result or result['path'].upper() == "NA":
			raise UpdateError("No path found in result %s for request %s" % (result, request))
		
		elif 'susize' not in result:
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("No susize found in result %s for request %s" % (result, request))
		
		# Do we need those additional checks ?
		elif 'sustatus' not in result:
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("No sustatus found in result %s for request %s" % (result, request))
		
		elif result['sustatus'].upper() != "Y":
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("Status different than Y in result %s for request %s" % (result, request))
		
		elif 'sunum' not in result:
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("No sunum found in result %s for request %s" % (result, request))
		
		elif result['sunum'] != str(request.sunum):
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("Mismatch sunum in result %s for request %s" % (result, request))
		
		elif 'series' not in result:
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("No series found in result %s for request %s" % (result, request))
		
		elif result['series'].lower() != request.data_series.drms_series.name.lower():
			# Because we don't know how to cope we just throw an exception
			raise UpdateError("Mismatch series name in result %s for request %s" % (result, request))
		
		else:
			if log is not None:
				log.debug("Found path %s for sunum %s with size %s", result['path'], request.sunum, result['susize'])
			request.path = result['path']
			request.size = int(result['susize'])


