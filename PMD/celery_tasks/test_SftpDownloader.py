#!/usr/bin/env python
import sys, os, pwd
import logging
import unittest

from SftpDownloader import SftpDownloader
from Exceptions import FileNotFound, ConnectionError, DownloadError

class SftpDownloaderTestCase(unittest.TestCase):
	"""Test Case for SftpDownloader"""
	server_address = "localhost"
	server_port = 22
	user_name = pwd.getpwuid(os.getuid()).pw_name
	timeout = 2
	window_size = 134217727
	password = None
	
	@classmethod
	def setUpClass(cls):
		pass
	
	@classmethod
	def tearDownClass(cls):
		pass
	
	def setUp(self):
		pass
	
	def tearDown(self):
		if os.path.exists("deleteme"):
			os.remove("deleteme")
	
	def get_downloader(self, server_address = None, user_name = None, password = None, server_port = None, window_size = None, timeout = None):
		downloader = SftpDownloader()
		downloader.setup(server_address or self.server_address, user_name or self.user_name, password or self.password, server_port or self.server_port, window_size or self.window_size, timeout or self.timeout)
		return downloader
	
	def test_setup(self):
		downloader = SftpDownloader()
		downloader.setup(self.server_address, self.user_name, self.password, self.server_port, self.window_size, self.timeout)
		self.assertEqual(downloader.server_address, self.server_address)
		self.assertEqual(downloader.user_name, self.user_name)
		self.assertEqual(downloader.password, self.password)
		self.assertEqual(downloader.server_port, self.server_port)
		self.assertEqual(downloader.timeout, self.timeout)
		self.assertEqual(downloader.window_size, self.window_size)
	
	def test_good_connection(self):
		downloader = self.get_downloader()
		downloader.open_connection(logging)
		self.assertIsNotNone(downloader.connection)
	
	def test_bad_connection(self):
		downloader = self.get_downloader("NotAServer")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
		
		downloader = self.get_downloader(user_name = "not_an_existing_username")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
	
		downloader = self.get_downloader(password = "wrong_password")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
		
		downloader = self.get_downloader(password = "/not_a_file")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		self.assertIsNone(downloader.connection)
	
	def test_close_good_connection(self):
		downloader = self.get_downloader()
		downloader.open_connection(logging)
		downloader.close_connection(logging)
		self.assertIsNone(downloader.connection)
	
	def test_close_bad_connection(self):
		downloader = self.get_downloader("NotAServer")
		with self.assertRaises(ConnectionError):
			downloader.open_connection(logging)
		downloader.close_connection(logging)
		self.assertIsNone(downloader.connection)
	
	def test_good_download(self):
		with open("/tmp/deletemein", "w") as f:
			f.write(str(range(1000)))
		downloader = self.get_downloader()
		downloader.download("/tmp/deletemein", "/tmp/deleteme")
		self.assertTrue(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
		os.remove("/tmp/deletemein")
	
	def test_file_not_found(self):
		downloader = self.get_downloader()
		with self.assertRaises(FileNotFound):
			downloader.download("/not_a_file", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
	
	def test_download_timeout(self):
		downloader = self.get_downloader()
		with self.assertRaises(DownloadError):
			downloader.download("/dev/random", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNotNone(downloader.connection)
	
	def test_download_errors(self):
		downloader = self.get_downloader()
		downloader.open_connection()
		# Close the connection to simulate a dropped connection
		downloader.connection.close()
		with self.assertRaises(DownloadError):
			downloader.download("/dev/random", "/tmp/deleteme")
		self.assertFalse(os.path.exists("/tmp/deleteme"))
		self.assertIsNone(downloader.connection)

if __name__ == '__main__':
	
	logging.basicConfig(level = logging.DEBUG, format='%(funcName)-12s %(levelname)-8s: %(message)s')
	
	unittest.main(buffer=True)
