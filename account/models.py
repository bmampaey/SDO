from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core import mail
from django.template.loader import render_to_string
from django.conf import settings

from global_config.models import GlobalConfig

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
	user = models.ForeignKey(User, related_name="messages")
	subject = models.TextField(help_text = "The subject of the message", default = "", blank=True, null=False)
	content = models.TextField(help_text = "The content of the message", blank=False, null=False)
	level = models.CharField(help_text = "The level of severity the message", max_length=7, choices = LEVELS, default = "INFO", blank=True, null=False)
	read = models.BooleanField(help_text = "If the message has been read", default=False, blank=True, null=False)
	
	class Meta:
		db_table = "user_message"

# We monkey patch the User model because the recommended way does not work
# https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#extending-the-existing-user-model

def send_message(self, subject_template, content_template, level = "INFO", kwargs={}, by_mail = False, copy_to_admins = False):
	
	subject = render_to_string(subject_template, kwargs)
	content = render_to_string(content_template, kwargs)
	UserMessage.objects.create(user = self, subject = subject, content = content, level = level)
	
	if by_mail == True:
		to = [self.email]
		if copy_to_admins:
			to += [admin[1] for admin in settings.ADMINS]
		
		mail.send_mail(subject.replace("\n", " "), content, None, to)
	
User.send_message = send_message
	
def disk_quota(self):
	try:
		user_disk_quota = self.profile.user_disk_quota
	except UserProfile.DoesNotExist:
		user_disk_quota = GlobalConfig.get("default_user_disk_quota", 50)
	# User disk quota is in GB
	return user_disk_quota * 1024*1024*1024

User.disk_quota = property(disk_quota)

def used_disk_quota(self):
	return sum([r.estimated_size() for r in self.exportdatarequest_set.all()])

User.used_disk_quota = property(used_disk_quota)


def remaining_disk_quota(self):
	return self.disk_quota - self.used_disk_quota

User.remaining_disk_quota = property(remaining_disk_quota)

def retention_time(self):
	try:
		user_retention_time = timedelta(days=self.profile.user_request_retention_time)
	except UserProfile.DoesNotExist:
		user_retention_time = timedelta(days=GlobalConfig.get("default_user_request_retention_time", 60))
	return user_retention_time

User.retention_time = property(retention_time)
