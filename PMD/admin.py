from django.contrib import admin

# Register your models here.
from PMD.models import GlobalConfig, DataSite, DataSeries, LocalDataLocation
from PMD.models import ROBDataLocation, JSOCDataLocation, SAODataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest
from PMD.models import  ExportDataRequest, ExportMetaDataRequest

class GlobalConfigAdmin(admin.ModelAdmin):
	list_display = ("name", "value", "python_type", "help_text")

class DataSiteAdmin(admin.ModelAdmin):
	list_display = ("name", "priority", "enabled", "data_download_protocol")

class ExportDataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "estimated_size", "expiration_date", "status", "requested")

class ExportMetaDataRequestAdmin(admin.ModelAdmin):
	list_display = ("user", "expiration_date", "status", "requested")


admin.site.register(GlobalConfig, GlobalConfigAdmin)
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

