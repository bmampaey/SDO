from datetime import datetime, timedelta
import dateutil.parser as date_parser

from django.db import models, IntegrityError

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
			variable, created = cls.objects.update_or_create(name=name, defaults={"value": str(value), "python_type": python_type, "help_text": help_text})
		except IntegrityError, why:
			# Hack the exception to add the variable name to the message
			why.args = ("Global configuration variable %s could not be set" % name, ) + why.args
			raise
	
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
			# Hack the exception to add the variable name to the message
			why.args = ("Global configuration variable %s is not set" % name, ) + why.args
			raise
		else:
			return cls.cast(variable.value, variable.python_type)

