from celery import Task
from PMD.routines.drms_data_location import break_url, get_http_client, call_jsoc_fetch, update_request

class DrmsDataLocator(Task):
	abstract = True
	
	def setup(self, url, timeout = 120, method = "GET"):
		self.server, self.url = break_url(url)
		self.timeout = timeout
		self.method = method
		self.http_client = None
	
	def get_client(self, reopen = False, log = None):
		if self.http_client is None or reopen:
			if log is not None:
				log.info("Opening http connection to %s", self.server)
			
			self.http_client = get_http_client(self.server, self.timeout)
		
		return self.http_client
	
	def locate(self, sunum, log = None):
		try:
			client = self.get_client(reopen = False, log = log)
			results =  call_jsoc_fetch(client, self.url, [sunum], method = self.method, log = log)
		except Exception, why:
			# TODO get socket exceptions and reopen connection
			log.error("Could not download %s from %s to %s", source, self.server, destination)
			raise
		
		return results[sunum]
	
	def update_request(self, request, result, log = None):
		update_request(request, result, log)

