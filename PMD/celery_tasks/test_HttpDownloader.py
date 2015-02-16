#!/usr/bin/env python
import sys, os
import logging
import unittest

import threading
from time import sleep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from HttpDownloader import HttpDownloader
from Exceptions import FileNotFound, ConnectionError, DownloadError

class RequestHandler(BaseHTTPRequestHandler):
	"""Handle HTTP requests"""
	
	#Handler for the GET requests
	def do_GET(self):
		if self.path == "/ok":
			logging.info("Received ok request")
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			# Send the html message
			self.wfile.write("ok")
			return
		
		elif self.path == "/time_out":
			logging.info("Received time_out request")
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			sleep(10)
			# Send the html message
			self.wfile.write("time_out")
			return
		
		elif self.path == "/server_error":
			logging.info("Received server_error request")
			self.send_error(500, 'Server error')
		
		else:
			logging.info("Received unknown request")
			self.send_error(404, 'File Not Found: %s' % self.path)


class HttpDownloaderTestCase(unittest.TestCase):
	"""Test Case for HttpDownloader"""
	server_address = "localhost"
	server_port = 8080
	timeout = 5
	method = "GET"
	
	@classmethod
	def setUpClass(cls):
		cls.server = HTTPServer((cls.server_address, cls.server_port), RequestHandler)
		cls.server.allow_reuse_address = True
		server_thread = threading.Thread(target=cls.server.serve_forever)
		server_thread.daemon = True
		server_thread.start()
	
	@classmethod
	def tearDownClass(cls):
		cls.server.shutdown()
	
	def setUp(self):
		pass
	
	def tearDown(self):
		if os.path.exists("/tmp/deleteme"):
			os.remove("/tmp/deleteme")
	
	def get_downloader(self, server_address = None, server_port = None, timeout = None, method = None):
		downloader = HttpDownloader()
		downloader.setup(server_address or self.server_address, server_port or self.server_port, timeout or self.timeout, method or self.method)
		return downloader
	
	def test_setup(self):
		downloader = HttpDownloader()
		downloader.setup(self.server_address, self.server_port, self.timeout, self.method)
		self.assertEqual(downloader.server_address, self.server_address)
		self.assertEqual(downloader.server_port, self.server_port)
		self.assertEqual(downloader.timeout, self.timeout)
		self.assertEqual(downloader.method, self.method)
	
	def test_good_connection(self):
		downloader = self.get_downloader()
		downloader.open_connection(logging)
		self.assertIsNotNone(downloader.connection)
	
	def test_bad_connection(self):
		downloader = self.get_downloader("NotAServer")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
		
		downloader = self.get_downloader("127.0.0.2")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
	
	def test_good_download(self):
		downloader = self.get_downloader()
		downloader.download("/ok", "/tmp/deleteme")
		self.assertTrue(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
	
	def test_file_not_found(self):
		downloader = self.get_downloader()
		with self.assertRaises(FileNotFound):
			downloader.download("/not_a_file", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
	
	def test_download_timeout(self):
		downloader = self.get_downloader()
		with self.assertRaises(DownloadError):
			downloader.download("/time_out", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
	
	def test_download_errors(self):
		downloader = self.get_downloader()
		with self.assertRaises(DownloadError):
			downloader.download("/server_error", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNone(downloader.connection)

if __name__ == '__main__':
	
	logging.basicConfig(level = logging.DEBUG, format='%(funcName)-12s %(levelname)-8s: %(message)s')
	
	unittest.main(buffer=True)
