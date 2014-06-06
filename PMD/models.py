import os
from datetime import datetime, timedelta

from django.db import models
from datetime import datetime, timedelta
from DRMS.models import DRMSDataSeries
from django.forms.models import model_to_dict

import dateutil.parser as date_parser
from routines.vso_sum import call_vso_sum_put, call_vso_sum_alloc

class GlobalConfig(models.Model):
	PYTHON_TYPE_CHOICES = (
		("string", "string"),
		("int", "int"),
		("float", "float"),
		("datetime", "datetime (iso format)"),
		("timedelta", "timedelta (in seconds)"),
	)
	name = models.CharField(max_length = 20, primary_key = True)
	value = models.CharField(max_length = 80, blank=False, null=False)
	python_type = models.CharField(max_length = 9, blank=False, null=False, default = "string", choices = PYTHON_TYPE_CHOICES)
	help_text = models.CharField(max_length = 80, blank=True, null=True, default = None)
	
	class Meta:
		db_table = "global_config"
		verbose_name = "Global configuration variable"
	
	def __unicode__(self):
		return unicode(self.name)
	
	@classmethod
	def get(cls, name):
		variable = cls.objects.get(name=name)
		if variable.python_type == "string":
			return variable.value
		elif variable.python_type == "int":
			return int(variable.value)
		elif variable.python_type == "float":
			return float(variable.value)
		elif variable.python_type == "datetime":
			return date_parser.parse(variable.value)
		elif variable.python_type == "timedeta":
			return timedelta(seconds=int(variable.value))
		else:
			raise Exception("Unknown python type for global config variable " + name)

class DataSite(models.Model):
	name = models.CharField("Data site name.", max_length=12, primary_key = True)
	priority = models.PositiveIntegerField(help_text = "Priority of the data site. The higher the value, the higher the priority.", default=0, blank=True, unique = True)
	enabled = models.BooleanField(help_text = "Data site is to be used to download data.", default = True, blank=True)
	local = models.BooleanField(help_text = "Data site is to be considered local. Only one data site should be set as local.", default = False)
	contact = models.CharField(help_text = "Contact emails for the data site.", blank=True, max_length=200)
	data_download_protocol = models.CharField(help_text = "Protocol to download data.", max_length=12, default = "sftp", choices=[("sftp", "sftp"), ("http", "http")])
	data_download_server = models.CharField(help_text = "Address of the data server.", max_length=50)
	data_download_user = models.CharField(help_text = "User for the data server connection.", max_length=12, blank=True)
	data_download_password = models.CharField(help_text = "Password for the data server connection.", max_length=255, default=None, blank=True, null=True)
	data_download_port = models.IntegerField(help_text = "Port for the data server connection.", default=None, blank=True, null=True)
	data_download_timeout = models.IntegerField(help_text = "Timeout for the data download.", default=None, blank=True, null=True)
	data_location_table = models.CharField(help_text = "Name of the data location table/model for this data site.", max_length=20, blank=False, null=False)
	data_location_request_url = models.URLField(help_text = "URL to request data location on data server.", max_length=200)
	data_location_request_timeout = models.PositiveIntegerField(help_text = "Timeout in seconds before a data location request to the server is considered failed.", default=120, blank=True, null=False)
	data_location_request_max_attempts = models.PositiveIntegerField(help_text = "Maximal number of attempt to request data location to the server before giving up.", default=3, blank=True, null=False)
	data_location_request_max_size = models.PositiveIntegerField(help_text = "Maximal number of data location to request at the same time. A high value mean the request will be less frequent.", default=100, blank=True, null=False)
	data_location_request_max_delay = models.PositiveIntegerField(help_text = "Maximal time to wait for queries before sending to the server. A high value mean the request will be less frequent.", default=100, blank=True, null=False)
	data_location_proactive = models.BooleanField(help_text = "Data location for this data site will be pro-actively queried.", default = False)
	
	class Meta:
		db_table = "data_site"
		ordering = ["priority"]
		verbose_name = "Data site"
		verbose_name_plural = "Data sites"
	
	def __unicode__(self):
		return unicode(self.name)
	
	@property
	def data_location(self):
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
	data_series = models.OneToOneField(DRMSDataSeries, help_text="DRMS data series.", on_delete=models.DO_NOTHING, related_name='+', db_column = "name", primary_key=True)
	retention = models.PositiveIntegerField(help_text = "Default minimum number of days before deleting the data.", default=60, blank=True)
	forced_datasite = models.ForeignKey(DataSite, help_text="Data site name to download the data from. Override the data site priority.", default=None, blank=True, null=True, on_delete=models.SET_NULL, db_column = "forced_datasite")
	last_treated_recnum = models.IntegerField(help_text = "Last record number treated.", default=0, blank=True, null=True)
	db_table = models.CharField(help_text = "PMD table name for the data series.", max_length=20, blank=False, null=False)
	
	class Meta:
		db_table = "data_series"
		verbose_name = "Data series"
		verbose_name_plural = "Data series"
	
	def __unicode__(self):
		return unicode(self.data_series)
	
	def default_expiration_date(self, date = datetime.utcnow()):
		return date + timedelta(days = self.retention)
	
	def __set_models(self):
		import PMD.models as PMD_models
		for model_name in dir(PMD_models):
			try:
				PMD_model = getattr(PMD_models, model_name)
				if PMD_model._meta.db_table == self.db_table:
					self.__model = PMD_model
			except Exception:
				pass
	
	@property
	def model(self):
		if not hasattr(self, '__model'):
			self.__set_models()
		return self.__model
	
	@property
	def average_file_size(self):
		return self.model.average_file_size
	
	@property
	def hdu(self):
		return self.model.hdu
	
	def get_header_values(self, request):
		# We must translate the attributes name to the real keyword name
		if not hasattr(self, '__header_keywords'):
			self.__set_header_keywords_units_comments()
		values = model_to_dict(self.data_series.fits_header_model.objects.get(recnum=request.recnum))
		header_values = dict()
		for attname, keyword in self.__header_keywords.iteritems():
			header_values[keyword] = values[attname]
		return header_values
	
	def __set_header_keywords_units_comments(self):
		self.__header_keywords = dict([field.get_attname_column() for field in self.data_series.fits_header_model._meta.fields])
		self.__header_units = dict()
		self.__header_comments = dict()
		for fits_keyword in self.data_series.fits_keyword_model.objects.all():
			self.__header_units[fits_keyword.keyword] = fits_keyword.unit
			self.__header_comments[fits_keyword.keyword] = fits_keyword.comment
		
	
	def get_header_units(self):
		if not hasattr(self, '__header_units'):
			self.__set_header_keywords_units_comments()
		return self.__header_units
	
	def get_header_comments(self):
		if not hasattr(self, '__header_comments'):
			self.__set_header_keywords_units_comments()
		return self.__header_comments


########################
# Data Location models #
########################

class PMDDataLocation(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	recnum = models.IntegerField(help_text = "JSOC Record number", blank=False, null=False, default=0)
	path = models.CharField(help_text = "Path of the data at the data site.", max_length=255, blank=False, null=False)
	
	class Meta:
		abstract = True
		unique_together = (("data_series", "recnum"),)
	
	def __unicode__(self):
		return u"%s %s" % (self.data_series, self.recnum)
	
	# Must only be called from LocalDataLocation
	@classmethod
	def get_location(cls, request):
		return cls.objects.get(data_series = request.data_series, recnum = request.recnum)
	
	# Must only be called from LocalDataLocation
	@classmethod
	def _delete_location(cls, request):
		data_location = cls.objects.get(data_series = request.data_series, recnum = request.recnum)
		data_location.delete()
	
	# Must only be called from LocalDataLocation
	@classmethod
	def _create_location(cls, request):
		cache = GlobalConfig.get("cache")
		path = os.path.join(cache, request.data_series.data_series.name, "%s.%s" % (request.recnum, request.segment))
		cls.save_path(request, path)
		return path
	
	@classmethod
	def get_file_path(cls, request):
		return cls.get_location(request).path
	
	@classmethod
	def save_path(cls, request, path):
		data_location, created = cls.objects.get_or_create(data_series = request.data_series, recnum = request.recnum, defaults = dict(path = path))
		if not created:
			data_location.path = path
			data_location.save()


class DrmsDataLocation(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, primary_key=True)
	path = models.CharField(help_text = "Path of the data at the data site.", max_length=255, blank=False, null=False)
	
	class Meta:
		abstract = True
	
	def __unicode__(self):
		return u"%s D%d" % (self.data_series, self.sunum)
	
	def __file_path(self, slotnum, segment):
		return os.path.join(self.path, "S%05d" % slotnum, segment)
	
	# Must only be called from LocalDataLocation
	@classmethod
	def get_location(cls, request):
		return cls.objects.get(sunum = request.sunum)
	
	# Must only be called from LocalDataLocation
	@classmethod
	def _delete_location(cls, request):
		raise NotImplementedError
	
	# Must only be called from LocalDataLocation
	@classmethod
	def _create_location(cls, request):
		# Check first that the location doesn't exist yet
		try:
			path = cls.get_file_path(request)
		except cls.DoesNotExist:
			# Create a new location by calling the sum_svc
			# Do a vso_sum_alloc to get a directory
			if not hasattr(request, 'size') or not request.size:
				request.size = request.data_series.average_file_size
			path = call_vso_sum_alloc(request.data_series.name, request.sunum, request.size, vso_sum_alloc = GlobalConfig.get("vso_sum_alloc"))
			# Do a vso_sum_put to register the directory
			if not request.expiration_date:
				retention = request.data_series.retention
			else:
				retention = (request.expiration_date - datetime.now()).days
			call_vso_sum_put(request.data_series.name, request.sunum, path, retention, vso_sum_put = GlobalConfig.get("vso_sum_put"))
			cls.save_path(request, path)
		return path
	
	@classmethod
	def get_file_path(cls, request):
		return cls.get_location(request).__file_path(request.slotnum, request.segment)
	
	@classmethod
	def save_path(cls, request, path):
		data_location, created = cls.objects.get_or_create(data_series = request.data_series, sunum = request.sunum, defaults = dict(path = path))
		if not created:
			data_location.path = path
			data_location.save()


class LocalDataLocation(PMDDataLocation):
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the data from the system.", blank=False, null=False)
	last_request_date = models.DateTimeField(help_text = "Date at which the data was last requested.", blank=False, null=False, default = datetime.now())
	
	class Meta(DrmsDataLocation.Meta):
		db_table = "data_location"
		verbose_name = "Local data location"
	
	def save(self, *args, **kwargs):
		if self.expiration_date is None:
			self.expiration_date = self.data_series.default_expiration_date()
		super(LocalDataLocation, self).save(*args, **kwargs)
	
	@classmethod
	def get_location(cls, request):
		data_location = super(LocalDataLocation, cls).get_location(request)
		data_location.last_request_date = datetime.now()
		data_location.save()
		return data_location
	
	@classmethod
	def delete_location(cls, request):
		cls._delete_location(request)
	
	@classmethod
	def create_location(cls, request):
		return cls._create_location(request)
	
	@classmethod
	def save_path(cls, request, path):
		super(LocalDataLocation, cls).save_path(request, path)
		if request.expiration_date:
			data_location = cls.get_location(request)
			data_loaction.expiration_date = request.expiration_date
			data_location.save()

class ROBDataLocation(DrmsDataLocation):
	
	class Meta(DrmsDataLocation.Meta):
		db_table = "rob_data_location"
		verbose_name = "ROB data location"

class JSOCDataLocation(DrmsDataLocation):
	
	class Meta(DrmsDataLocation.Meta):
		db_table = "jsoc_data_location"
		verbose_name = "JSOC data location"

class SAODataLocation(DrmsDataLocation):
	
	class Meta(DrmsDataLocation.Meta):
		db_table = "sao_data_location"
		verbose_name = "SAO data location"

####################
# Meta Data models #
####################

class AiaLev1(models.Model):
	recnum = models.BigIntegerField(primary_key=True)
	sunum = models.BigIntegerField(blank=True, null=True)
	slotnum = models.IntegerField(blank=True, null=True)
	segment = models.TextField(blank=True)
	date_obs = models.DateTimeField(blank=True, null=True)
	wavelnth = models.FloatField(blank=True, null=True)
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	fsn = models.IntegerField(blank=True, null=True)
	
	# Global properties
	hdu = 1
	average_file_size = 12 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'aia_lev1'
		unique_together = (("t_rec_index", "fsn"),)
		verbose_name = "AIA Lev1"
	
	def __unicode__(self):
		return unicode("%s %s" % (self._meta.verbose_name, self.recnum))


class HmiIc45S(models.Model):
	recnum = models.BigIntegerField(primary_key=True)
	sunum = models.BigIntegerField(blank=True, null=True)
	slotnum = models.IntegerField(blank=True, null=True)
	segment = models.TextField(blank=True)
	date_obs = models.DateTimeField(blank=True, null=True)
	wavelnth = models.FloatField(blank=True, null=True)
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	camera = models.IntegerField(blank=True, null=True)
	
	# Global properties
	hdu = 1
	average_file_size = 20 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'hmi_ic_45s'
		unique_together = (("t_rec_index", "camera"),)
		verbose_name = "HMI M45s"
	
	def __unicode__(self):
		return unicode("%s %s" % (self._meta.verbose_name, self.recnum))


class HmiM45S(models.Model):
	recnum = models.BigIntegerField(primary_key=True)
	sunum = models.BigIntegerField(blank=True, null=True)
	slotnum = models.IntegerField(blank=True, null=True)
	segment = models.TextField(blank=True)
	date_obs = models.DateTimeField(blank=True, null=True)
	wavelnth = models.FloatField(blank=True, null=True)
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	camera = models.IntegerField(blank=True, null=True)
	
	# Global properties
	hdu = 1
	average_file_size = 20 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'hmi_m_45s'
		unique_together = (("t_rec_index", "camera"),)
		verbose_name = "HMI M45s"
	
	def __unicode__(self):
		return unicode("%s %s" % (self._meta.verbose_name, self.recnum))

