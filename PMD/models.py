from django.db import models
from datetime import datetime, timedelta
from DRMS.models import DRMSDataSeries

# Create your models here.
class DataSites(models.Model):
	name = models.CharField("Data site name.", max_length=12, primary_key = True)
	protocol = models.CharField(help_text = "Protocol to download data. I.e. scp, sftp, http, ...", max_length=12, default = "scp")
	server = models.CharField(help_text = "Address of the data server.", max_length=50)
	user = models.CharField(help_text = "User for the data server connection.", max_length=12, blank=True)
	port = models.IntegerField(help_text = "Port for the data server connection.", default=None, blank=True, null=True)
	priority = models.PositiveIntegerField(help_text = "Priority of the data site. The higher the value, the higher the priority.", default=0, blank=True, unique = True)
	contact = models.CharField(help_text = "Contact emails for the data site.", blank=True, max_length=200)
	enabled = models.BooleanField(help_text = "Data site is to be used to download data.", default = True, blank=True)
	local = models.BooleanField(help_text = "Data site is to be considered local. Only one data site should be set as local.", default = False)
	data_location_table = models.CharField(help_text = "Name of the data location table/model for this data site.", max_length=20, blank=False, null=False)
	data_location_query_url = models.URLField(help_text = "URL to query data location on data server.", max_length=200)
	data_location_query_timeout = models.PositiveIntegerField(help_text = "Timeout in seconds before a data location query to the server is considered failed.", default=120, blank=True, null=False)
	data_location_query_max_attempts = models.PositiveIntegerField(help_text = "Maximal number of attempt to query data location to the server before giving up.", default=3, blank=True, null=False)
	data_location_query_max_size = models.PositiveIntegerField(help_text = "Maximal number of data location to query at the same time. A high value mean the query will be less frequent.", default=100, blank=True, null=False)
	data_location_query_max_priority = models.PositiveIntegerField(help_text = "Maximal accumulation of queries priority before the query is actually made to the server. A high value mean the query will be less frequent.", default=100, blank=True, null=False)
	proactively_query_location = models.BooleanField(help_text = "Data location for this data site will be pro-actively queried.", default = False)
	
	class Meta:
		db_table = "data_sites"
		ordering = ["priority"]
		verbose_name = "Data site"
		verbose_name_plural = "Data sites"
	
	def __unicode__(self):
		return unicode(self.name)
	
	@property
	def data_location_model(self):
		if not hasattr(self, '__data_location_model'):
			import PMD.models as PMD_models
			for model_name in dir(PMD_models):
				try:
					PMD_model = getattr(PMD_models, model_name)
					if PMD_model._meta.db_table == self.data_location_table:
						self.__data_location_model = PMD_model
				except Exception:
					pass
		return self.__data_location_model

class DataSeries(models.Model):
	name = models.ForeignKey(DRMSDataSeries, help_text="DRMS data series.", on_delete=models.DO_NOTHING, related_name='+', db_column = "name", primary_key=True)
	retention = models.PositiveIntegerField(help_text = "Default minimum number of days before deleting the data.", default=60, blank=True)
	prefered_datasite = models.ForeignKey(DataSites, help_text="Prefered data site name to download the data from. Will override the data site priority if set.", default=None, blank=True, null=True, on_delete=models.SET_NULL, db_column = "prefered_datasite")
	
	class Meta:
		db_table = "data_series"
		verbose_name = "Data series"
		verbose_name_plural = "Data series"
	
	def __unicode__(self):
		return unicode(self.name)
	
	def default_retention_date(self, date = datetime.utcnow()):
		return date + timedelta(days = self.retention)

class DownloadRequest(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, null=False)
	slotnum = models.IntegerField(help_text = "JSOC Slot number", blank=False, null=False, default=0)
	segment = models.CharField(help_text = "JSOC Segment name.", max_length=255, blank=False, null=False)
	priority = models.PositiveIntegerField(help_text = "Priority of download. The higher the value, the higher the priority.", default=0, blank=True)
	status = models.CharField(help_text = "Download status.", max_length=8, blank=False, null=False, default = "NEW")
	requested = models.DateTimeField(help_text = "Date of insertion into the download queue.", null=False, auto_now_add = True)
	updated = models.DateTimeField(help_text = "Date of last status update.", null=False, auto_now = True)
	
	class Meta:
		unique_together = (("sunum", "slotnum"),)
		db_table = "download_request"
		ordering = ["priority", "requested"]
		get_latest_by = "requested"
		verbose_name = "Download request"
		verbose_name_plural = "Download requests"
		
	def __unicode__(self):
		return u"%s D%d/S%06d %s" % (self.data_series, self.sunum, self.slotnum, self.status)
	
	def __lt__(self, other):
		'''Return true if the priority is bigger'''
		if self.priority > other.priority:
			return True
		elif self.priority == other.priority:
			return self.requested < other.requested
		else:
			return False


class DataLocationQuery(models.Model):
	data_site = models.ForeignKey(DataSites, help_text="Data site name to query the data location from.", on_delete=models.PROTECT, db_column = "data_site_name")
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, null=False)
	slotnum = models.IntegerField(help_text = "JSOC Slot number", blank=False, null=False, default=0)
	segment = models.CharField(help_text = "JSOC Segment name.", max_length=255, blank=False, null=False)
	priority = models.PositiveIntegerField(help_text = "Priority of download. The higher the value, the higher the priority.", default=0, blank=True)
	requested = models.DateTimeField(help_text = "Date of insertion into the data location query queue.", null=False, auto_now_add = True)
	
	class Meta:
		db_table = "data_location_query"
		ordering = ["priority", "requested"]
		get_latest_by = "requested"
		verbose_name = "Data location query"
		verbose_name_plural = "Data location queries"
	
	def __unicode__(self):
		return u"%s D%d/S%06d" % (self.data_series, self.sunum, self.slotnum)
	
	def __lt__(self, other):
		'''Return true if the priority is bigger'''
		if self.priority > other.priority:
			return True
		elif self.priority == other.priority:
			return self.requested < other.requested
		else:
			return False


class DataLocation(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, null=False)
	slotnum = models.IntegerField(help_text = "JSOC Slot number", blank=False, null=False, default=0)
	path = models.CharField(help_text = "Path of the data at the data site.", max_length=255, blank=False, null=False)
	
	class Meta:
		unique_together = (("sunum", "slotnum"),)
		abstract = True
	
	def __unicode__(self):
		return u"%s D%d/S%06d" % (self.data_series, self.sunum, self.slotnum)
	
	@property
	def full_path(self):
		return "%s/D%s/S%06d" % (self.path, self.sunum, self.slotnum)


class ROBDataLocation(DataLocation):
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the data from the system.", blank=False, null=False)
	last_request_date = models.DateTimeField(help_text = "Date at which the data was last requested.", blank=False, null=False, default = datetime.utcnow())
	
	class Meta(DataLocation.Meta):
		db_table = "rob_data_location"
		verbose_name = "ROB data location"
	
	def save(self, *args, **kwargs):
		if self.expiration_date is None:
			self.expiration_date = DataSites.objects().get(pk=self.data_series).default_retention_date()
		super(DataLocation, self).save(*args, **kwargs)

class JSOCDataLocation(DataLocation):
	
	class Meta(DataLocation.Meta):
		db_table = "jsoc_data_location"
		verbose_name = "JSOC data location"

class SAODataLocation(DataLocation):
	
	class Meta(DataLocation.Meta):
		db_table = "sao_data_location"
		verbose_name = "SAO data location"
