from django.contrib import admin
from account.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "user_request_retention_time", "user_disk_quota")

admin.site.register(UserProfile, UserProfileAdmin)