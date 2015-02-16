import os
import httplib
import time
import socket
from celery import Task

from Exceptions import FileNotFound, ConnectionError, DownloadError

class HttpDownloader(Task):
	abstract = True
	
	def setup(self, server_address, server_port = 80, timeout = 120, method = "GET"):
		self.server_address = server_address
		self.server_port = server_port
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
	
	def download(self, source, destination, log = None):
		if log is not None:
			log.debug("Downloading file %s from %s", source, self.server_address)
			start = time.time()
		
		# Open the connection
		connection = self.open_connection(log = log)
		
		# Make the request
		try:
			connection.request(self.method, source)
			response = connection.getresponse()
			response_content = response.read()
		except socket.timeout, why:
			if log is not None:
				log.error("Timeout while downloading file %s from server %s: %s", source, connection.host, why)
			
			raise DownloadError("Timeout while downloading file %s from server %s: %s" % (source, connection.host, why))
		
		except Exception, why:
			if log is not None:
				log.error("Error while downloading file %s from server %s: %s", source, connection.host, why)
			
			# Close the connection for the future requests
			self.close_connection()
			
			raise DownloadError("Error while downloading file %s from server %s: %s" % (source, connection.host, why))
		
		if log is not None:
			log.debug("Status: %s, reason: %s", response.status, response.reason)
		
		if response.status == httplib.NOT_FOUND or response.status == httplib.MOVED_PERMANENTLY:
			raise FileNotFound("Could not download file %s from server %s. Status: %s. Reason: %s." % (source, connection.host, response.status, response.reason))
		
		elif response.status != 200:
			raise DownloadError("Could not download file %s from server %s. Status: %s. Reason: %s." % (source, connection.host, response.status, response.reason))
			
		elif log is not None:
			log.debug("Download of file %s from %s took %s seconds", source, connection.host, time.time() - start)
		
		# Write the response to destination
		try:
			with open(destination, 'wb') as f:
				f.write(response_content)
		except Exception, why:
			if log is not None:
				log.error("Could not write to file %s: %s", destination, why)
			
			# Remove the partial download
			try:
				os.remove(destination)
			except OSError:
				pass
			
			raise DownloadError("Error while writing to file %s: %s" % (destination, why))

