from datetime import datetime
from PMD.models import DataSite, DataSeries
from django.db import models

class Request(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, null=False)
	slotnum = models.IntegerField(help_text = "JSOC Slot number", blank=False, null=False, default=0)
	segment = models.CharField(help_text = "JSOC Segment name.", max_length=255, blank=False, null=False)
	recnum = models.IntegerField(help_text = "JSOC Record number", blank=True, null=True, default=0)
	status = models.CharField(help_text = "Request status.", max_length=8, blank=False, null=False, default = "NEW")
	priority = models.PositiveIntegerField(help_text = "Priority of execution. The higher the value, the higher the priority.", default=0, blank=True)
	requested = models.DateTimeField(help_text = "Date of request.", null=False, auto_now_add = True)
	updated = models.DateTimeField(help_text = "Date of last status update.", null=False, auto_now = True)
	
	class Meta:
		abstract = True
		ordering = ["priority", "requested"]
		get_latest_by = "requested"
	
	def __unicode__(self):
		return u"%s D%d/S%05d %s" % (self.data_series, self.sunum, self.slotnum, self.status)
	
	def __lt__(self, other):
		'''Return true if the priority is bigger'''
		if self.priority > other.priority:
			return True
		elif self.priority == other.priority:
			return self.requested < other.requested
		else:
			return False
	
	# Not a good idea to overide the init method of models
	@classmethod
	def create_from_meta_data(cls, meta_data, priority = 0):
		request = cls(data_series = DataSeries.objects.get(db_table = meta_data._meta.db_table), sunum = meta_data.sunum, slotnum = meta_data.slotnum, segment = meta_data.segment, recnum = meta_data.recnum, priority = priority)
		request.size = request.data_series.average_file_size
		return request

class DataDownloadRequest(Request):
	data_site = models.ForeignKey(DataSite, help_text="Name of the data site from which to download the data from.", on_delete=models.PROTECT, db_column = "data_site_name")
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the data from the system.", blank=True, null=True)
	remote_file_path = models.CharField(help_text = "File path at the remote data site", max_length=255, blank=True, null=True, default=None)
	local_file_path = models.CharField(help_text = "File path at the local data site", max_length=255, blank=True, null=True, default=None)

class DataLocationRequest(Request):
	data_site = models.ForeignKey(DataSite, help_text="Name of the data site from which to find the location of the data from.", on_delete=models.PROTECT, db_column = "data_site_name")

class DataDeleteRequest(Request):
	pass

class MetaDataUpdateRequest(Request):
	pass

