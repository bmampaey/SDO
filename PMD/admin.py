from django.contrib import admin

# Register your models here.
from PMD.models import GlobalConfig, DataSite, DataSeries, LocalDataLocation
from PMD.models import ROBDataLocation, JSOCDataLocation, SAODataLocation
from PMD.models import DataDownloadRequest, DataLocationRequest, DataDeleteRequest, MetaDataUpdateRequest

admin.site.register(GlobalConfig)
admin.site.register(DataSite)
admin.site.register(DataSeries)
admin.site.register(LocalDataLocation)
admin.site.register(ROBDataLocation)
admin.site.register(JSOCDataLocation)
admin.site.register(SAODataLocation)
admin.site.register(DataDownloadRequest)
admin.site.register(DataLocationRequest)
admin.site.register(DataDeleteRequest)
admin.site.register(MetaDataUpdateRequest)
