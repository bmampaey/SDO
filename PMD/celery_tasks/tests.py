#!/usr/bin/env python
import sys, os
import logging
import unittest
from celery import Celery

app = Celery('app', broker='amqp://', backend='amqp://')

# This should go
sys.path.append('/home/benjmam/SDO')

class Request:
	def __init__(self,remote_path, local_path):
		self.remote_file_path = remote_path
		self.local_file_path = local_path

from HttpDownloader import HttpDownloader

class HttpDownloaderTestCase(unittest.TestCase):
	"""Test Case for HttpDownloader Task"""
	def setUp(self):
		self.destination = "/tmp/deleteme"
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def tearDown(self):
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def create_data_downloader(self, name, server, timeout = 20, method = "GET"):
		@app.task(base=HttpDownloader, name=name, bind=True)
		def data_downloader(self, request):
			self.download(request.remote_file_path, request.local_file_path, logging)
			return request
		
		data_downloader.setup(server = server, timeout = timeout, method = method)
		
		return data_downloader
	
	def test_spacepole(self):
		logging.info("HttpDownloader")
		data_downloader = self.create_data_downloader("spacepole", "www.spacepole.be")
		request = Request("/", self.destination)
		request = data_downloader(request)
		self.assertTrue(os.path.exists(self.destination))
	
	def test_JSOC(self):
		logging.info("HttpDownloader")
		data_downloader = self.create_data_downloader("JSOC_HttpDownloader", "jsoc.stanford.edu", 20)
		request = Request("/SUM68/D509698083/S00000/image_lev1.fits", self.destination)
		request = data_downloader(request)
		self.assertTrue(os.path.exists(self.destination))

from SftpDownloader import SftpDownloader

class SftpDownloaderTestCase(unittest.TestCase):
	"""Test Case for SftpDownloader Task"""
	def setUp(self):
		self.destination = "/tmp/deleteme"
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def tearDown(self):
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def create_data_downloader(self, name, host_name, user_name, password, port = 22, window_size = 134217727, timeout = None):
		@app.task(base=SftpDownloader, name=name, bind=True)
		def data_downloader(self, request):
			self.download(request.remote_file_path, request.local_file_path, logging)
			return request
		
		data_downloader.setup(host_name, user_name, password, port, window_size, timeout)
		
		return data_downloader
	
	def test_JSOC(self):
		logging.info("SftpDownloader")
		data_downloader = self.create_data_downloader("JSOC_SftpDownloader", "jsocport.stanford.edu", "jsocexp", password = "./id_rsa", port = 55000)
		request = Request("/SUM68/D509698083/S00000/image_lev1.fits", self.destination)
		request = data_downloader(request)
		self.assertTrue(os.path.exists(self.destination))

if __name__ == '__main__':
	
	logging.basicConfig(level = logging.DEBUG, format='%(funcName)-12s %(levelname)-8s: %(message)s')
	
	unittest.main(buffer=True)
