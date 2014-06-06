from celery import Task
from PMD.routines.sftp_data_download import get_ssh_client, sftp_download

class SftpDownloader(Task):
	abstract = True
	
	def setup(self, host_name, user_name, password = None, port = 22, window_size = 134217727, timeout = None):
		self.host_name = host_name
		self.user_name = user_name
		self.password = password
		self.port = port
		self.window_size = window_size
		self.timeout = timeout
		self.ssh_client = None
	
	def get_client(self, reopen = False, log = None):
		if self.ssh_client is None or reopen:
			if log is not None:
				log.info("Opening ssh connection to %s", self.host_name)
			
			self.ssh_client = get_ssh_client(self.host_name, self.user_name, self.password, self.port, self.window_size, self.timeout)
		
		return self.ssh_client
	
	def download(self, source, destination, log = None):
		try:
			client = self.get_client(reopen = False, log = log)
			sftp_download(client, source, destination, log)
		except Exception, why:
			# TODO get socket exceptions and reopen connection
			if log is not None:
				log.error("Could not download %s from %s to %s", source, self.host_name, destination)
			raise

