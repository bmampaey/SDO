#!/usr/bin/python
import httplib
import urlparse
import time

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

def http_download(http_client, source, destination, method = "GET", log = None):
	'''Download data through http'''
	if log is not None:
		log.debug("Downloading file %s from %s", source, http_client.host)
		start = time.time()
	
	http_client.request(method, source)
	response = http_client.getresponse()
	response_content = response.read()
	
	if log is not None:
		log.debug("Download of file %s from %s took %s seconds", source, http_client.host, time.time() - start)
	
	with open(destination, 'wb') as f:
		f.write(response_content)
