from django.contrib import admin

# Register your models here.
from PMD.models import DataSite, DataSeries, LocalDataLocation
from PMD.models import ROBDataLocation, JSOCDataLocation, SAODataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest
from PMD.models import  ExportDataRequest, ExportMetaDataRequest


class DataSiteAdmin(admin.ModelAdmin):
	list_display = ("name", "priority", "enabled", "data_download_protocol")

class ExportDataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "estimated_size", "expiration_date", "status", "requested")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ('data_series', 'requested', 'recnums', 'task_ids')
		return self.readonly_fields

class ExportMetaDataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "expiration_date", "status", "requested")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ('data_series', 'requested', 'recnums', 'task_ids')
		return self.readonly_fields


admin.site.register(DataSite, DataSiteAdmin)
admin.site.register(DataSeries)
# admin.site.register(LocalDataLocation)
# admin.site.register(ROBDataLocation)
# admin.site.register(JSOCDataLocation)
# admin.site.register(SAODataLocation)
admin.site.register(DataDownloadRequest)
admin.site.register(DataLocationRequest)
admin.site.register(DataDeleteRequest)
admin.site.register(MetaDataUpdateRequest)
admin.site.register(ExportDataRequest, ExportDataRequestAdmin)
admin.site.register(ExportMetaDataRequest, ExportMetaDataRequestAdmin)

