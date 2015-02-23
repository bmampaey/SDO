import os
import httplib
import paramiko
import time
import socket
import errno
from celery import Task
from app import app

class FileNotFound(Exception):
	pass

class ConnectionError(Exception):
	pass

class DownloadError(Exception):
	pass


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

class SftpDownloader(Task):
	abstract = True
	
	def setup(self, server_address, user_name, password = None, server_port = 22, window_size = 134217727, timeout = None):
		self.server_address = server_address
		self.user_name = user_name
		self.password = password
		self.server_port = server_port
		self.window_size = window_size
		self.timeout = timeout
		self.connection = None
	
	def open_connection(self, log = None):
		"""Open a sftp connection to the server"""
		if self.connection is None:
			if log is not None:
				log.info("Opening sftp connection to %s", self.server_address)
			
			try:
				self.connection = paramiko.SSHClient()
				self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				
				if self.password is None: # We let paramiko try to connect to a authentification agent or find a private key_file in ~/.ssh
					self.connection.connect(self.server_address, port = self.server_port, username = self.user_name, timeout = self.timeout)
				
				elif os.path.isfile(self.password): # If password is a file we assume it is a key_filename
					self.connection.connect(self.server_address, port = self.server_port, username = self.user_name, key_filename = self.password, timeout = self.timeout)
				
				else: # If a private key_file in ~/.ssh needs a password it will be used, otherwise it will use the password directly
					self.connection.connect(self.server_address, port = self.server_port, username = self.user_name, password = self.password, timeout = self.timeout)
				
				# Increasing the window size may increase the speed but is more risky
				if self.window_size is not None:
					self.connection._transport.window_size = self.window_size
			
			except Exception, why:
				self.connection = None
				if log is not None:
					log.error("Error while opening connection to server %s: %s", self.server_address, why)
				raise ConnectionError("Could not open connection to server %s: %s." % (self.server_address, why))
		
		return self.connection
	
	def close_connection(self, log = None):
		"""Close the sftp connection to the server"""
		if self.connection is not None:
			if log is not None:
				log.info("Closing sftp connection to %s", self.server_address)
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
			sftp = connection.open_sftp()
			sftp.get_channel().settimeout(self.timeout)
			sftp.get(source, destination)
			sftp.close()
		
		except socket.timeout, why:
			if log is not None:
				log.error("Timeout while downloading file %s from server %s: %s", source, self.server_address, why)
			
			# Remove the partial download
			try:
				os.remove(destination)
			except OSError:
				pass
			
			raise DownloadError("Timeout while downloading file %s from server %s: %s" % (source, self.server_address, why))
		
		except IOError, why:
			if why.errno == errno.ENOENT:
				raise FileNotFound("Could not download file %s from server %s. File is missing." % (source, self.server_address))
			else:
				# Close the connection for the future requests
				self.close_connection()
			
				# Remove the partial download
				try:
					os.remove(destination)
				except OSError:
					pass
				
				raise DownloadError("Error while downloading file %s from server %s: %s" % (source, self.server_address, why))
			
		except Exception, why:
			if log is not None:
				log.error("Error while downloading file %s from server %s: %s", source, self.server_address, why)
			
			# Close the connection for the future requests
			self.close_connection()
			
			# Remove the partial download
			try:
				os.remove(destination)
			except OSError:
				pass
			
			raise DownloadError("Error while downloading file %s from server %s: %s" % (source, self.server_address, why))
			
		if log is not None:
				log.debug("Download of file %s took %s seconds", source, time.time() - start)

def create_data_downloader(data_site, log = None):
	"""Create specific data downloader task for each data site"""
	if log is not None:
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

