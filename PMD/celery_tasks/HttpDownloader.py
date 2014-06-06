from celery import Task
from PMD.routines.http_data_download import get_http_client, http_download

class HttpDownloader(Task):
	abstract = True
	
	def setup(self, server = "sidc.oma.be", timeout = 120, method = "GET"):
		self.server = server
		self.timeout = timeout
		self.method = method
		self.http_client = None
	
	def get_client(self, reopen = False, log = None):
		if self.http_client is None or reopen:
			if log is not None:
				log.info("Opening http connection to %s", self.server)
			
			self.http_client = get_http_client(self.server, self.timeout)
		
		return self.http_client
	
	def download(self, source, destination, log = None):
		try:
			client = self.get_client(reopen = False, log = log)
			http_download(client, source, destination, method = self.method, log = log)
		except Exception, why:
			# TODO get socket exceptions and reopen connection
			log.error("Could not download %s from %s to %s", source, self.server, destination)
			raise

