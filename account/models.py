from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User, primary_key = True, related_name="profile")
	user_request_retention_time = models.IntegerField(help_text = "The minimum retention time in days for user request. Leave blank to use default.", default=30, blank=False, null=False)
	user_disk_quota = models.FloatField(help_text = "The maximum disk size in GB for user request. Leave blank to use default.", default=None, blank=False, null=False)
	
	class Meta:
		db_table = "user_profile"

class UserMessage(models.Model):
	LEVELS = (
		("INFO", "INFO"),
		("SUCCESS", "SUCCESS"),
		("WARNING", "WARNING"),
		("ERROR", "ERROR"),
	)
	user = models.ForeignKey(User, primary_key = True, related_name="messages")
	message = models.TextField(help_text = "A message for the user", blank=False, null=False)
	level = models.CharField(help_text = "The level of severity the message", max_length=7, choices = LEVELS, default = "INFO", blank=True, null=False)
	read = models.BooleanField(help_text = "If the message has been read", default=False, blank=True, null=False)
	
	class Meta:
		db_table = "user_message"
