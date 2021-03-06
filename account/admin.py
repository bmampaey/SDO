from django.contrib import admin
from account.models import UserProfile, UserMessage

class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "user_request_retention_time", "user_disk_quota")

class UserMessageAdmin(admin.ModelAdmin):
	list_display = ("user", "level", "subject", "read")


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserMessage, UserMessageAdmin)
