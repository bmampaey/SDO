from django.contrib import admin
from global_config.models import GlobalConfig

class GlobalConfigAdmin(admin.ModelAdmin):
	list_display = ("name", "value", "python_type", "help_text")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ("name",)
		return self.readonly_fields

admin.site.register(GlobalConfig, GlobalConfigAdmin)