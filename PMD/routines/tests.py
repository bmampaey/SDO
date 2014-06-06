#!/usr/bin/env python
import sys, os
import logging
import unittest

import http_data_download

class HttpDataDownloadTestCase(unittest.TestCase):
	"""Test Case for http_data_download routines"""
	def setUp(self):
		self.server = "www.google.be"
		self.path = "/index.html"
		self.destination = "/tmp/deleteme"
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def tearDown(self):
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def test_break_url(self):
		url = "http://" + self.server + self.path
		# Check the correct splitting of urls
		self.assertEqual(http_data_download.break_url(url), (self.server, self.path))
		
		# Refuse non http urls
		with self.assertRaises(Exception):
			http_data_download.break_url("ftp://omaftp.oma.be")
	
	def test_get_http_client(self):
		# Check we can connect
		http_data_download.get_http_client(self.server)
	
	def test_http_download(self):
		# Check succesfull download
		http_client = http_data_download.get_http_client(self.server)
		http_data_download.http_download(http_client, self.path, self.destination)
		self.assertTrue(os.path.exists(self.destination))
	
	def test_http_download_failure(self):
		# Check failure download
		http_client = http_data_download.get_http_client(self.server)
		http_data_download.http_download(http_client, "I probably dont exists", self.destination)
		self.assertTrue(os.path.exists(self.destination))
	
	
	def test_http_download_timeout(self):
		# Check timeout download
		http_client = http_data_download.get_http_client(self.server, timeout = 0)
		import socket
		with self.assertRaises(socket.error) as cm:
			http_data_download.http_download(http_client, self.path, self.destination, logging)
		print "Exception", cm.exception
		logging.debug("Exception %s", cm.exception)
		self.assertTrue(cm.exception.errno == 115 or cm.exception.errno == 101)

import sftp_data_download

class SftpDataDownloadTestCase(unittest.TestCase):
	"""Test Case for sftp_data_download routines"""
	def setUp(self):
		self.host_name = "db2.sdodb.oma.be"
		self.user_name = "rob"
		self.private_rsa_key = "~/.ssh/id_rsa"
		self.password = "aiahmieve"
		self.source = "/bin/ls"
		self.destination = "/tmp/deleteme"
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def tearDown(self):
		if os.path.exists(self.destination):
			os.remove(self.destination)
	
	def test_get_ssh_client(self):
		# Check we can connect
		logging.debug("Test ssh connection to %s", self.host_name)
		sftp_data_download.get_ssh_client(self.host_name, self.user_name, password = self.password, timeout = 10)
	
	def test_sftp_download(self):
		# Check download
		ssh_client = sftp_data_download.get_ssh_client(self.host_name, self.user_name, password = self.password, timeout = 10)
		sftp_data_download.sftp_download(ssh_client, self.source, self.destination, logging)
		self.assertTrue(os.path.exists(self.destination))

import drms_data_location

class DrmsDataLocationTestCase(unittest.TestCase):
	"""Test Case for drms_data_location routines"""
	def setUp(self):
		self.server = "www.google.be"
		self.path = "/index.html"
		self.jsoc_url = "http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_fetch_VSO"
		self.remote_file_path = "/SUM68/D509698083"
		self.sunum = 509698083
	
	def tearDown(self):
		pass
	
	def test_break_url(self):
		
		url = "http://" + self.server + self.path
		# Check the correct splitting of urls
		self.assertEqual(drms_data_location.break_url(url), (self.server, self.path))
		
		# Refuse non http urls
		with self.assertRaises(Exception):
			drms_data_location.break_url("ftp://omaftp.oma.be")
		
		# Refuse empty urls
		with self.assertRaises(Exception):
			drms_data_location.break_url("http://")
	
	def test_get_http_client(self):
		# Check we can connect
		drms_data_location.get_http_client(self.server)
		
		drms_data_location.get_http_client("")
	
	def test_call_jsoc_fetch(self):
		# Check succesfull download
		server, url = drms_data_location.break_url(self.jsoc_url)
		http_client = drms_data_location.get_http_client(server)
		results = drms_data_location.call_jsoc_fetch(http_client, url, [self.sunum])
		print results
		
		self.assertEqual(results[self.sunum]['path'], self.remote_file_path)

	def test_update_request(self):
		result = {u'sunum': u'509698083', u'path': u'/SUM68/D509698083', u'susize': u'325572', u'sustatus': u'Y', u'series': u'aia.lev1'}
		from collections import namedtuple
		class Request:
			data_series = namedtuple("W", ["name"])(result["series"])
			sunum = result["sunum"]
		request = Request()
		drms_data_location.update_request(request, result, logging)
		self.assertEqual(request.path, result["path"])
		self.assertIsNotNone(request.size, result["susize"])



if __name__ == '__main__':
	
	logging.basicConfig(level = logging.DEBUG, format='%(funcName)-12s %(levelname)-8s: %(message)s')
	
	unittest.main(buffer=True)

