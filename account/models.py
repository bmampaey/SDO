from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
	user = models.OneToOneField(User, primary_key = True, related_name="profile")
	user_request_retention_time = models.IntegerField(help_text = "The minimum retention time in days for user request. Leave blank to use default.", default=30, blank=False, null=False)
	user_disk_quota = models.FloatField(help_text = "The maximum disk size in GB for user request. Leave blank to use default.", default=None, blank=False, null=False)
	
	class Meta:
		db_table = "user_profile"