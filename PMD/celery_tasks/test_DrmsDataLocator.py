#!/usr/bin/env python
import sys, os
import logging
import unittest

import threading
from time import sleep
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from DrmsDataLocator import DrmsDataLocator
from Exceptions import LocateError, ConnectionError, SetupError

class DataLocationRequest:
	class DataSeries:
		pass
	
	def __init__(self, sunum, path, size, drms_series_name):
		self.sunum = sunum
		self.path = path
		self.size = size
		self.data_series = self.DataSeries()
		self.data_series.drms_series = self.DataSeries()
		self.data_series.drms_series.name = drms_series_name

class RequestHandler(BaseHTTPRequestHandler):
	"""Handle HTTP requests"""
	
	#Handler for the GET requests
	def do_GET(self):
		url_parts = urlparse.urlparse(self.path)
		data = urlparse.parse_qs(url_parts.query)
		
		if url_parts.path == "/ok":
			logging.info("Received ok request")
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			message = '{"count":1,"size":8478870,"dir":"","data":{"%s":{"sunum":"%s","series":"aia.lev1","path":"\/SUM66\/D%s","sustatus":"Y","susize":"8478870"}},"requestid":"","method":"url_quick","protocol":"as-is","wait":0,"status":0}'
			self.wfile.write(message % tuple(data["sunum"]*3))
			return
		
		elif url_parts.path == "/time_out":
			logging.info("Received time_out request")
			self.send_response(200)
			self.send_header('Content-type','html/text')
			self.end_headers()
			sleep(10)
			# Send the html message
			self.wfile.write("time_out")
			return
		
		elif url_parts.path == "/unknown_sunum":
			logging.info("Received unknown_sunum request")
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			message = '{"count":1,"size":0,"dir":"","data":{"%s":{"sunum":"%s","series":"NA","path":"NA","sustatus":"I","susize":"0"}},"requestid":"","method":"url_quick","protocol":"as-is","wait":0,"status":0}'
			self.wfile.write(message % tuple(data["sunum"]*2))
			return
		
		elif url_parts.path == "/bad_sunum":
			logging.info("Received bad_sunum request")
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			message='{"status":4,"error":"Invalid argument on entry, \'sunum=no\'.\n"}'
			self.wfile.write(message)
			
		
		elif url_parts.path == "/no_data":
			logging.info("Received unknown_sunum request")
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			message = '{"count":1,"size":0,"dir":"","requestid":"","method":"url_quick","protocol":"as-is","wait":0,"status":0}'
			self.wfile.write(message)
			return
		
		elif url_parts.path == "/missing_sunum":
			logging.info("Received unknown_sunum request")
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()
			# Send the html message
			message = '{"count":1,"size":0,"dir":"","data":{"%s":{"sunum":"%s","series":"NA","path":"NA","sustatus":"I","susize":"0"}},"requestid":"","method":"url_quick","protocol":"as-is","wait":0,"status":0}'
			self.wfile.write(message % (0, 0))
			return
		
		elif url_parts.path == "/server_error":
			logging.info("Received server_error request")
			self.send_error(500, 'Server error')
		
		else:
			logging.info("Received unknown request")
			self.send_error(404, 'File Not Found: %s' % self.path)


class DrmsDataLocatorTestCase(unittest.TestCase):
	"""Test Case for DrmsDataLocator"""
	server_address = "localhost"
	server_port = 8080
	timeout = 2
	method = "GET"
	
	def url(self, path = "", server_address = None, server_port = None):
		URL = "http://%s" % (server_address or self.server_address)
		if server_port is not None or self.server_port is not None:
			URL += ":%s" % (server_port or self.server_port)
		
		URL += "/%s" % path
		return URL
	
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
		pass
	
	def test_setup(self):
		locator = DrmsDataLocator()
		locator.setup(self.url(), self.timeout, self.method)
		self.assertEqual(locator.server_address, self.server_address)
		self.assertEqual(locator.server_port, self.server_port)
		self.assertEqual(locator.timeout, self.timeout)
		self.assertEqual(locator.method, self.method)
	
	def test_good_connection(self):
		locator = DrmsDataLocator()
		locator.setup(self.url())
		locator.open_connection(logging)
		self.assertIsNotNone(locator.connection)
	
	def test_bad_connection(self):
		locator = DrmsDataLocator()
		locator.setup(self.url(server_address = "NotAServer"))
		with self.assertRaises(ConnectionError):
			locator.open_connection(logging)
		self.assertIsNone(locator.connection)
		
		locator = DrmsDataLocator()
		locator.setup(self.url(server_address = "127.0.0.2"))
		with self.assertRaises(ConnectionError):
			locator.open_connection(logging)
		self.assertIsNone(locator.connection)
	
	def test_good_location(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("ok"))
		sunum = 590106369
		results = locator.locate(sunum, logging)
		expected = {
			590106369: {u'path': u'/SUM66/D590106369',
			u'series': u'aia.lev1',
			u'sunum': u'590106369',
			u'susize': u'8478870',
			u'sustatus': u'Y'}
		}
		self.assertDictEqual(expected, results)
		self.assertIsNotNone(locator.connection)
	
	def test_invalid_path(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("invalid_path"))
		sunum = 590106369
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		self.assertIsNotNone(locator.connection)
	
	def test_download_timeout(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("time_out"))
		sunum = 590106369
		
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		self.assertIsNotNone(locator.connection)
	
	def test_server_error(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("server_error"))
		sunum = 590106369
		
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		
		self.assertIsNotNone(locator.connection)
	
	def test_unknown_sunum(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("unknown_sunum"))
		sunum = 590106369
		results = locator.locate(sunum, logging)
		expected = {
			590106369: {u'path': u'NA',
			u'series': u'NA',
			u'sunum': u'590106369',
			u'susize': u'0',
			u'sustatus': u'I'}
		}
		self.assertDictEqual(expected, results)
		self.assertIsNotNone(locator.connection)
	
	def test_bad_sunum(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("bad_sunum"))
		sunum = 590106369
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		self.assertIsNotNone(locator.connection)
	
	def test_no_data(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("no_data"))
		sunum = 590106369
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		self.assertIsNotNone(locator.connection)
	
	def test_missing_sunum(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("missing_sunum"))
		sunum = 590106369
		results = locator.locate(sunum, logging)
		self.assertIsNotNone(locator.connection)
		self.assertIsInstance(results, dict)
	
	def test_crash_connection(self):
		locator = DrmsDataLocator()
		locator.setup(self.url("ok"))
		connection = locator.open_connection()
		connection.auto_open = 0
		connection.close()
		sunum = 590106369
		with self.assertRaises(LocateError):
			results = locator.locate(sunum, logging)
		self.assertIsNone(locator.connection)

if __name__ == '__main__':
	
	logging.basicConfig(level = logging.DEBUG, format='%(funcName)-12s %(levelname)-8s: %(message)s')
	
	unittest.main(buffer=True)
