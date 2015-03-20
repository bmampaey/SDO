from django.contrib import admin

# Register your models here.
from PMD.models import DataSite, DataSeries, LocalDataLocation
from PMD.models import ROBDataLocation, JSOCDataLocation, SAODataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetadataUpdateRequest
from PMD.models import  ExportDataRequest, ExportMetadataRequest


class DataSiteAdmin(admin.ModelAdmin):
	list_display = ("name", "priority", "enabled", "data_download_protocol", "data_location_protocol")

class ExportDataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "estimated_size", "expiration_date", "status", "requested")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ('data_series', 'requested', 'recnums', 'task_ids')
		return self.readonly_fields

class ExportMetadataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "expiration_date", "status", "requested")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ('data_series', 'requested', 'recnums', 'task_ids')
		return self.readonly_fields

class DataRequestAdmin(admin.ModelAdmin):
	list_display = ("data_series", "sunum", "recnum", "requested", "status")
	
	def get_readonly_fields(self, request, obj=None):
		if obj:
			return self.readonly_fields + ('requested')
		return self.readonly_fields


admin.site.register(DataSite, DataSiteAdmin)
admin.site.register(DataSeries)
# admin.site.register(LocalDataLocation)
# admin.site.register(ROBDataLocation)
# admin.site.register(JSOCDataLocation)
# admin.site.register(SAODataLocation)
admin.site.register(DataDownloadRequest, DataRequestAdmin)
admin.site.register(DataLocationRequest, DataRequestAdmin)
admin.site.register(DataDeleteRequest, DataRequestAdmin)
admin.site.register(MetadataUpdateRequest, DataRequestAdmin)
admin.site.register(ExportDataRequest, ExportDataRequestAdmin)
admin.site.register(ExportMetadataRequest, ExportMetadataRequestAdmin)

