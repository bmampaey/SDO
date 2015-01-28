import os
from datetime import datetime, timedelta
import dateutil.parser as date_parser
import shutil
import logging
import uuid

from django.db import models, IntegrityError
from django.forms.models import model_to_dict
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import receiver

# djorm-pgarray allow to use postgres arrays
# To install: "sudo pip install djorm-pgarray"
from djorm_pgarray.fields import BigIntegerArrayField, TextArrayField, ArrayField, IntegerArrayField

from celery.task.control import revoke as revoke_task

from DRMS.models import DRMSDataSeries, AiaLev1FitsHeader, HmiIc45sFitsHeader, HmiM45sFitsHeader, HmiMharp720SFitsHeader, HmiSharp720SFitsHeader
from routines.vso_sum import call_vso_sum_put, call_vso_sum_alloc


# TODO: check how to store array of uuid

# TODO check how to config logging in django
logging.basicConfig(level = logging.DEBUG, format = "%(levelname)s %(funcName)s %(message)s")
# Get an instance of a logger
log = logging.getLogger(__name__)



class GlobalConfig(models.Model):
	PYTHON_TYPE_CHOICES = (
		("string", "string"),
		("bool", "bool"),
		("int", "int"),
		("float", "float"),
		("datetime", "datetime (iso format)"),
		("timedelta", "timedelta (in seconds)"),
	)
	name = models.CharField(max_length = 80, primary_key = True)
	value = models.CharField(max_length = 80, blank=False, null=False)
	python_type = models.CharField(max_length = 12, blank=False, null=False, default = "string", choices = PYTHON_TYPE_CHOICES)
	help_text = models.CharField(max_length = 80, blank=True, null=True, default = None)
	
	class Meta:
		db_table = "global_config"
		ordering = ["name"]
		verbose_name = "Global configuration variable"
	
	def __unicode__(self):
		return unicode(self.name)
	
	@staticmethod
	def cast(value, python_type):
		""" Cast the value to the one of the known python type """
		if python_type == "string":
			return value
		elif python_type == "bool":
			return value.lower() in ['true', 't', 'y', 'yes', '1']
		elif python_type == "int":
			return int(value)
		elif python_type == "float":
			return float(value)
		elif python_type == "datetime":
			return date_parser.parse(value)
		elif python_type == "timedelta":
			return timedelta(seconds=float(value))
		else:
			raise Exception("Unknown python type %" +  python_type)
	
	@classmethod
	def set(cls, name, value, help_text = "Please, set description."):
		if isinstance(value, datetime):
			python_type = "datetime"
			value = value.isoformat()
		elif isinstance(value, timedelta):
			python_type = "timedelta"
			value = value.total_seconds()
		else:
			python_type = type(value).__name__
			if python_type not in [a for (a,b) in cls.PYTHON_TYPE_CHOICES]:
				raise Exception("Invalid python type for global config variable %s with value %s" % (name, value))
		
		try:
			variable, created = cls.objects.get_or_create(name=name, defaults={"value": str(value), "python_type": python_type, "help_text": help_text})
		except IntegrityError:
			pass
		else:
			if not created:
				variable.value = value
				variable.save()
	
	@classmethod
	def get(cls, name, default = None):
		#import pdb; pdb.set_trace()
		try:
			variable = cls.objects.get(name=name)
		except cls.DoesNotExist:
			cls.set(name, default, help_text = "Automatically created from application, please check and set decription")
			return default
		else:
			return cls.cast(variable.value, variable.python_type)
	
	
	@classmethod
	def get_or_fail(cls, name):
		try:
			variable = cls.objects.get(name=name)
		except cls.DoesNotExist, why:
			# Hack the exception to add the looked up variable name to the message
			why.args = ("Global configuration variable %s is not set" % name, ) + why.args
			raise
		else:
			return cls.cast(variable.value, variable.python_type)

class UserProfile(models.Model):
	user = models.OneToOneField(User, primary_key = True, related_name="profile")
	user_request_retention_time = models.IntegerField(help_text = "The minimum retention time in days for user request. Leave blank to use default.", default=30, blank=False, null=False)
	user_disk_quota = models.FloatField(help_text = "The maximum disk size in GB for user request. Leave blank to use default.", default=None, blank=False, null=False)
	
	class Meta:
		db_table = "user_profile"

class DataSite(models.Model):
	name = models.CharField("Data site name.", max_length=12, primary_key = True)
	priority = models.PositiveIntegerField(help_text = "Priority of the data site. The higher the value, the higher the priority.", default=0, blank=True, unique = True)
	enabled = models.BooleanField(help_text = "Data site is to be used to download data.", default = True, blank=True)
	contact = models.CharField(help_text = "Contact emails for the data site.", blank=True, max_length=200)
	data_download_protocol = models.CharField(help_text = "Protocol to download data.", max_length=12, default = "sftp", choices=[("sftp", "sftp"), ("http", "http")])
	data_download_server = models.CharField(help_text = "Address of the data server.", max_length=50)
	data_download_user = models.CharField(help_text = "User for the data server connection.", max_length=12, blank=True)
	data_download_password = models.CharField(help_text = "Password for the data server connection.", max_length=255, default=None, blank=True, null=True)
	data_download_port = models.IntegerField(help_text = "Port for the data server connection.", default=None, blank=True, null=True)
	data_download_timeout = models.IntegerField(help_text = "Timeout for the data download.", default=None, blank=True, null=True)
	data_download_max_attempts = models.PositiveIntegerField(help_text = "Maximal number of attempt to download data from the server before giving up.", default=3, blank=True, null=False)
	data_location_table = models.CharField(help_text = "Name of the data location table/model for this data site.", max_length=20, blank=False, null=False)
	data_location_request_url = models.URLField(help_text = "URL to request data location on data server.", max_length=200)
	data_location_request_timeout = models.PositiveIntegerField(help_text = "Timeout in seconds before a data location request to the server is considered failed.", default=120, blank=True, null=False)
	data_location_request_max_attempts = models.PositiveIntegerField(help_text = "Maximal number of attempt to request data location to the server before giving up.", default=3, blank=True, null=False)
	data_location_request_max_size = models.PositiveIntegerField(help_text = "Maximal number of data location to request at the same time. A high value mean the request will be less frequent.", default=100, blank=True, null=False)
	data_location_proactive = models.BooleanField(help_text = "Data location for this data site will be pro-actively queried.", default = False)
	
	class Meta:
		db_table = "data_site"
		ordering = ["-priority"]
		verbose_name = "Data site"
		verbose_name_plural = "Data sites"
	
	def __unicode__(self):
		return unicode(self.name)
	
	def __set_models(self):
		data_location_models = PMDDataLocation.__subclasses__() + DrmsDataLocation.__subclasses__()
		for data_location_model in data_location_models:
			if data_location_model._meta.db_table == self.data_location_table:
				self.__data_location_model = data_location_model
				break
		else:
			raise Exception("No data location model with table name %s" % self.data_location_table)
	
	@property
	def data_location(self):
		if not hasattr(self, '__data_location_model'):
			self.__set_models()
		return self.__data_location_model

class DataSeries(models.Model):
	record_table = models.CharField(help_text = "PMD record table name for the data series.", max_length=20, primary_key=True, validators=[RegexValidator("\w+", "Can only contain letters, numbers and underscore.")])
	drms_series = models.OneToOneField(DRMSDataSeries, help_text="DRMS data series name.", on_delete=models.DO_NOTHING, related_name='+', blank=False, null=False)
	retention = models.PositiveIntegerField(help_text = "Default minimum number of days before deleting the data.", default=60, blank=True)
	forced_datasite = models.ForeignKey(DataSite, help_text="Data site name to download the data from. Override the data site priority.", default=None, blank=True, null=True, on_delete=models.SET_NULL)
	
	class Meta:
		db_table = "data_series"
		verbose_name = "Data series"
		verbose_name_plural = "Data series"
	
	def __unicode__(self):
		return unicode(self.name)
	
	def default_expiration_date(self, date = datetime.utcnow()):
		return date + timedelta(days = self.retention)
	
	@property
	def name(self):
		return self.record_table
	
	def __set_models(self):
		data_series_record_models = PmdRecord.sub_models()
		if self.record_table in data_series_record_models:
			self.__record_model = data_series_record_models[self.record_table]
		else:
			raise Exception("No record model with table name %s" % self.record_table)
	
	@property
	def record(self):
		if not hasattr(self, '__record_model'):
			self.__set_models()
		return self.__record_model
	
	@property
	def average_file_size(self):
		return self.record.average_file_size
	
	@property
	def hdu(self):
		return self.record.hdu
	
	def get_header_values(self, recnum):
		# We must translate the attributes name to the real keyword name
		if not hasattr(self, '__header_keywords'):
			self.__set_header_keywords_units_comments()
		values = model_to_dict(self.drms_series.fits_header_model.objects.get(recnum=recnum))
		header_values = dict()
		for attname, keyword in self.__header_keywords.iteritems():
			header_values[keyword] = values[attname]
		return header_values
	
	def __set_header_keywords_units_comments(self):
		self.__header_keywords = dict([field.get_attname_column() for field in self.drms_series.fits_header_model._meta.fields])
		self.__header_units = dict()
		self.__header_comments = dict()
		for fits_keyword in self.drms_series.fits_keyword_model.objects.all():
			self.__header_units[fits_keyword.keyword] = fits_keyword.unit
			self.__header_comments[fits_keyword.keyword] = fits_keyword.comment
		
	def get_header_keywords(self):
		if not hasattr(self, '__header_keywords'):
			self.__set_header_keywords_units_comments()
		return self.__header_keywords.values()
	
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
	recnum = models.BigIntegerField(help_text = "JSOC Record number", blank=False, null=False, default=0)
	path = models.CharField(help_text = "Path of the data at the data site.", max_length=255, blank=False, null=False)
	
	class Meta:
		abstract = True
		unique_together = (("data_series", "recnum"),)
	
	def __unicode__(self):
		return u"%s %s" % (self.data_series, self.recnum)
	
	@classmethod
	def get_location(cls, request):
		return cls.objects.get(data_series = request.data_series, recnum = request.recnum)
	
	@classmethod
	def get_file_path(cls, request):
		data_location = cls.get_location(request)
		return data_location.path
	
	@classmethod
	def save_path(cls, request, path):
		# TODO In django 1.7 use update_or_create
		data_location, created = cls.objects.get_or_create(data_series = request.data_series, recnum = request.recnum, defaults = dict(path = path))
		if not created:
			data_location.path = path
			data_location.save()


class LocalDataLocation(PMDDataLocation):
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the data from the system.", blank=False, null=False)
	last_request_date = models.DateTimeField(help_text = "Date at which the data was last requested.", blank=False, null=False, default = datetime.now())
	
	class Meta(PMDDataLocation.Meta):
		db_table = "data_location"
		verbose_name = "Local data location"
	
	def save(self, *args, **kwargs):
		if self.expiration_date is None:
			self.expiration_date = self.data_series.default_expiration_date()
		super(LocalDataLocation, self).save(*args, **kwargs)
	
	@classmethod
	def has_expired(cls, request):
		data_location = cls.get_location(request)
		if data_location.expiration_date > datetime.now():
			return False
		else:
			return True
	
	@classmethod
	def last_requested(cls, request):
		data_location = cls.get_location(request)
		return data_location.last_request_date
	
	@classmethod
	def update_expiration_date(cls, request, expiration_date = None, force = False):
		data_location = cls.get_location(request)
		# If expiration_date is None, it will increase the expiration date by the default retention time
		if force or expiration_date is None or data_location.expiration_date < expiration_date:
			data_location.expiration_date = expiration_date
			data_location.save()
		
		return data_location.expiration_date
	
	@classmethod
	def create_location(cls, request):
		cache_path = GlobalConfig.get_or_fail("data_cache_path")
		path = os.path.join(cache_path, request.data_series.name, "%s.%s" % (request.recnum, request.segment))
		cls.save_path(request, path)
		return path
	
	@classmethod
	def get_file_path(cls, request):
		# For local data location we update the request date
		data_location = cls.get_location(request)
		data_location.last_request_date = datetime.now()
		data_location.save()
		return data_location.path
	
	@classmethod
	def save_path(cls, request, path):
		# For local data location we set the expiration date
		super(LocalDataLocation, cls).save_path(request, path)
		if request.expiration_date:
			data_location = cls.get_location(request)
			data_location.expiration_date = request.expiration_date
			data_location.save()
	
	@classmethod
	def delete_location(cls, request):
		# We allow that the data location does not exist
		try:
			data_location = cls.get_location(request)
		except cls.DoesNotExist:
			return
		data_location.delete()

# Register a django signal so that when a LocalDataLocation is deleted, the corresponding files are also deleted
@receiver(signals.post_delete, sender=LocalDataLocation)
def delete_local_data_location_files(sender,  instance, using, **kwargs):
	log.info("local_data_location %s, delete files %s", instance, instance.path)
	try:
		os.remove(instance.path)
	except Exception, why:
		log.error("local_data_location %s, could not delete files %s: %s", instance, instance.path, str(why))

class DrmsDataLocation(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, primary_key=True)
	path = models.CharField(help_text = "Path of the data at the data site.", max_length=255, blank=False, null=False)
	
	class Meta:
		abstract = True
	
	def __unicode__(self):
		return u"%s D%d" % (self.data_series, self.sunum)
	
	@classmethod
	def get_location(cls, request):
		return cls.objects.get(sunum = request.sunum)
	
	@classmethod
	def get_file_path(cls, request):
		data_location = cls.get_location(request)
		return os.path.join(data_location.path, "S%05d" % request.slotnum, request.segment)
	
	@classmethod
	def save_path(cls, request, path):
		data_location, created = cls.objects.get_or_create(sunum = request.sunum, defaults = dict(data_series = request.data_series, path = path))
		if not created:
			data_location.path = path
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

######################
# PMD record models  #
######################

class PmdRecord(models.Model):
	recnum = models.BigIntegerField(primary_key=True)
	sunum = models.BigIntegerField(blank=True, null=True)
	slotnum = models.IntegerField(blank=True, null=True)
	segment = models.TextField(blank=True)
	date_obs = models.DateTimeField(blank=True, null=True)
	
	class Meta:
		abstract = True
	
	def __unicode__(self):
		return unicode("%s %s" % (self._meta.verbose_name, self.recnum))
	
	@classmethod
	def sub_models(cls):
		return dict([(model._meta.db_table, model) for model in cls.__subclasses__()])

class AiaLev1Record(PmdRecord):
	wavelnth = models.FloatField(blank=True, null=True)
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	fsn = models.IntegerField(blank=True, null=True)
	fits_header = models.OneToOneField(AiaLev1FitsHeader, related_name = "latest", to_field="recnum", db_column="recnum", db_constraint=False, on_delete=models.DO_NOTHING)
	
	# Global properties
	hdu = 1
	average_file_size = 12 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'aia_lev1'
		unique_together = (("t_rec_index", "fsn"),)
		ordering = ["t_rec_index"]
		verbose_name = "AIA Lev1"
	
	@property
	def filename(self):
		return "AIA.%s.%04d.%s" % (self.date_obs.strftime("%Y%m%d_%H%M%S"), self.wavelnth, self.segment)


class HmiIc45SRecord(PmdRecord):
	wavelnth = models.FloatField(blank=True, null=True)
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	camera = models.IntegerField(blank=True, null=True)
	fits_header = models.OneToOneField(HmiIc45sFitsHeader, related_name = "latest", to_field="recnum", db_column="recnum", db_constraint=False, on_delete=models.DO_NOTHING)
	
	# Global properties
	hdu = 1
	average_file_size = 20 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'hmi_ic_45s'
		unique_together = (("t_rec_index", "camera"),)
		ordering = ["t_rec_index"]
		verbose_name = "HMI M45s"
		
	@property
	def filename(self):
		return "HMI.%s.%s" % (self.date_obs.strftime("%Y%m%d_%H%M%S"), self.segment)


class HmiM45SRecord(PmdRecord):
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	camera = models.IntegerField(blank=True, null=True)
	fits_header = models.OneToOneField(HmiM45sFitsHeader, related_name = "latest", to_field="recnum", db_column="recnum", db_constraint=False, on_delete=models.DO_NOTHING)
	
	# Global properties
	hdu = 1
	average_file_size = 20 * 1024 * 1024
	
	class Meta:
		managed = False
		db_table = 'hmi_m_45s'
		unique_together = (("t_rec_index", "camera"),)
		ordering = ["t_rec_index"]
		verbose_name = "HMI M45s"
		
	@property
	def filename(self):
		return "HMI.%s.%s" % (self.date_obs.strftime("%Y%m%d_%H%M%S"), self.segment)

class HmiMharp720SRecord(PmdRecord):
	quality = models.IntegerField(blank=True, null=True)
	t_rec_index = models.BigIntegerField(blank=True, null=True)
	harpnum = models.IntegerField(blank=True, null=False)
	fits_header = models.OneToOneField(HmiMharp720SFitsHeader, related_name = "latest", to_field="recnum", db_column="recnum", db_constraint=False, on_delete=models.DO_NOTHING)
	
	lat_min = models.FloatField(blank=True, null=True)
	lon_min = models.FloatField(blank=True, null=True)
	lat_max = models.FloatField(blank=True, null=True)
	lon_max = models.FloatField(blank=True, null=True)
	t_frst1 = models.DateTimeField(blank=True, null=True)
	t_last1 = models.DateTimeField(blank=True, null=True)
	nacr = models.IntegerField(blank=True, null=True)
	size_acr = models.FloatField(blank=True, null=True)
	area_acr = models.FloatField(blank=True, null=True)
	mtot = models.FloatField(blank=True, null=True)
	noaa_ars = IntegerArrayField(blank=True, null=True)

	# Global properties
	hdu = 0
	average_file_size = 20 * 1024
	
	class Meta:
		managed = False
		db_table = 'hmi_mharp_720s'
		unique_together = (("t_rec_index", "harpnum"),)
		ordering = ["t_rec_index"]
		verbose_name = "HMI Mharp720s"
		
	@property
	def filename(self):
		return "HMI.%s.%s.%s" % (self.date_obs.strftime("%Y%m%d_%H%M%S"), self.harpnum, self.segment)


########################
# Data request models  #
########################

class DataRequest(models.Model):
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.PROTECT, db_column = "data_series_name")
	sunum = models.BigIntegerField(help_text = "JSOC Storage Unit number", blank=False, null=False)
	slotnum = models.IntegerField(help_text = "JSOC Slot number", blank=False, null=False, default=0)
	segment = models.CharField(help_text = "JSOC Segment name.", max_length=255, blank=False, null=False)
	recnum = models.BigIntegerField(help_text = "JSOC Record number", blank=True, null=True, default=0)
	status = models.CharField(help_text = "Request status.", max_length=8, blank=False, null=False, default = "NEW")
	priority = models.PositiveIntegerField(help_text = "Priority of execution. The higher the value, the higher the priority.", default=0, blank=True)
	requested = models.DateTimeField(help_text = "Date of request.", null=False, auto_now_add = True)
	updated = models.DateTimeField(help_text = "Date of last status update.", null=False, auto_now = True)
	
	class Meta:
		abstract = True
		ordering = ["-priority", "requested"]
		get_latest_by = "requested"
	
	def __unicode__(self):
		return u"%s D%d/S%05d %s" % (self.data_series.name, self.sunum, self.slotnum, self.status)
	
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
	def create_from_record(cls, record, priority = 0):
		request = cls(data_series = DataSeries.objects.get(record_table = record._meta.db_table), sunum = record.sunum, slotnum = record.slotnum, segment = record.segment, recnum = record.recnum, priority = priority)
		request.size = request.data_series.average_file_size
		return request

class DataDownloadRequest(DataRequest):
	data_site = models.ForeignKey(DataSite, help_text="Name of the data site from which to download the data from.", on_delete=models.PROTECT, db_column = "data_site_name")
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the data from the system.", blank=True, null=True)
	remote_file_path = models.CharField(help_text = "File path at the remote data site", max_length=255, blank=True, null=True, default=None)
	local_file_path = models.CharField(help_text = "File path at the local data site", max_length=255, blank=True, null=True, default=None)
	
	class Meta(DataRequest.Meta):
		db_table = "data_download_request"
		verbose_name = "Data download request"

class DataLocationRequest(DataRequest):
	data_site = models.ForeignKey(DataSite, help_text="Name of the data site from which to find the location of the data from.", on_delete=models.PROTECT, db_column = "data_site_name")
	
	class Meta(DataRequest.Meta):
		db_table = "data_location_request"
		verbose_name = "Data location request"

class DataDeleteRequest(DataRequest):
	
	class Meta(DataRequest.Meta):
		db_table = "data_delete_request"
		verbose_name = "Data delete request"

class MetaDataUpdateRequest(DataRequest):
	old_recnum = models.BigIntegerField(help_text = "JSOC Record number", blank=True, null=True, default=0)
	
	class Meta(DataRequest.Meta):
		db_table = "meta_data_update_request"
		verbose_name = "Meta-data update request"

########################
# User request models  #
########################

class UserRequest(models.Model):
	user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
	data_series = models.ForeignKey(DataSeries, help_text="Name of the data series the data belongs to.", on_delete=models.DO_NOTHING, db_column = "data_series_name")
	recnums = BigIntegerArrayField(help_text = "List of recnums to export")
	expiration_date = models.DateTimeField(help_text = "Date after which it is ok to delete the request.", blank=False, null=False)
	status = models.CharField(help_text = "Request status.", max_length=20, blank=False, null=False, default = "NEW")
	requested = models.DateTimeField(help_text = "Date of request.", null=False, default = datetime.now())
	updated = models.DateTimeField(help_text = "Date of last status update.", null=False, auto_now = True)
	#task_id = models.CharField(help_text = "Task id.", max_length=36, blank=True, null=True, default = None)
	#task_ids = ArrayField(dbtype="uuid", type_cast = lambda x: uuid.UUID(x))
	task_ids = ArrayField(dbtype="varchar(36)")
	
	class Meta:
		abstract = True
		ordering = ["requested"]
		get_latest_by = "requested"
	
	def save(self, *args, **kwargs):
		if self.expiration_date is None:
			try:
				retention_time = timedelta(days=self.user.profile.user_request_retention_time)
			except UserProfile.DoesNotExist:
				retention_time = timedelta(days=GlobalConfig.get("default_user_request_retention_time", 60))
			self.expiration_date = self.requested + retention_time
		super(UserRequest, self).save(*args, **kwargs)
	
	@property
	def type(self):
		return self._meta.verbose_name
	
	def revoke(self, terminate=False):
		if self.task_ids:
			revoke_task(self.task_ids, terminate=terminate)
	
	def __unicode__(self):
		return u"%s %s" % (self.user, self.requested)


class ExportDataRequest(UserRequest):
	
	class Meta(UserRequest.Meta):
		db_table = "export_data_request"
		verbose_name = "Export data request"
		
	@property
	def name(self):
		return self.requested.strftime("%Y%m%d_%H%M%S")
	
	@property
	def export_path(self):
		cache_path = GlobalConfig.get_or_fail("export_cache_path")
		path = os.path.join(cache_path, self.user.username, self.data_series.name, self.name)
		return path
	
	@property
	def ftp_path(self):
		ftp_url = GlobalConfig.get_or_fail("export_ftp_url")
		path = os.path.join(ftp_url, self.user.username, self.data_series.name, self.name)
		return path
	
	def estimated_size(self, human_readable = False):
		if self.recnums is None:
			size = 0
		else:
			size = self.data_series.record.average_file_size * len(self.recnums)
		if human_readable:
			for suffix in ["B", "KB", "MB", "GB", "TB"]: 
				if size >= 1024:
					size/=1024
				else:
					break
			return "%d %s" % (size, suffix)
		else:
			return size
	
	# For displaying in tables
	column_headers = ["Requested", "Data Series", "Size", "Expires", "Status"]
	
	@property
	def row_fields(self):
		return [
			self.requested,
			self.data_series.name,
			self.estimated_size(human_readable =True),
			self.expiration_date,
			self.status.lower()
		]


# Register a django signal so that when a ExportDataRequest is deleted, the corresponding files are also deleted
@receiver(signals.post_delete, sender=ExportDataRequest)
def delete_export_data_files(sender, instance, using, **kwargs):
	# Cancel the background task
	if instance.task_ids:
		log.info("user request %s, cancel tasks %s", str(instance), instance.task_ids)
		instance.revoke()
	
	# Delete the files
	log.info("user request %s, delete files %s", str(instance), instance.export_path)
	shutil.rmtree(instance.export_path, ignore_errors = True)
	
class ExportMetaDataRequest(UserRequest):
	
	class Meta(UserRequest.Meta):
		db_table = "export_meta_data_request"
		verbose_name = "Export meta-data request"
		
	@property
	def name(self):
		return "%s.%s" % (self.data_series.name, self.requested.strftime("%Y%m%d_%H%M%S"))
	
	@property
	def export_path(self):
		cache_path = GlobalConfig.get_or_fail("export_cache_path")
		path = os.path.join(cache_path, self.user.username, self.name + ".csv")
		return path
	
	@property
	def ftp_path(self):
		ftp_url = GlobalConfig.get_or_fail("export_ftp_url")
		path = os.path.join(ftp_url, self.user.username, self.name + ".csv")
		return path
	
	# For displaying in tables
	column_headers = ["Requested", "Data Series", "Length", "Expires", "Status"]
	
	@property
	def row_fields(self):
		return [
			self.requested,
			self.data_series.name,
			len(self.recnums),
			self.expiration_date,
			self.status.lower()
		]


# Register a django signal so that when a ExportMetaDataRequest is deleted, the corresponding files are also deleted
@receiver(signals.post_delete, sender=ExportMetaDataRequest)
def delete_export_meta_data_files(sender, instance, using, **kwargs):
	# Cancel the background task
	if instance.task_ids:
		log.info("user request %s, cancel tasks %s", str(instance), instance.task_ids)
		instance.revoke()
	
	# Delete the files
	log.info("user request %s, delete files %s", str(instance), instance.export_path)
	try:
		os.remove(instance.export_path)
	except Exception, why:
			log.error("user request %s, could not delete files %s: %s", instance, instance.export_path, str(why))
