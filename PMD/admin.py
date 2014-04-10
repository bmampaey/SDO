from django.contrib import admin

# Register your models here.
from PMD.models import DataSites, DataSeries, DownloadRequest, DataLocationQuery, ROBDataLocation, JSOCDataLocation, SAODataLocation
admin.site.register(DataSites)
admin.site.register(DataSeries)
admin.site.register(DownloadRequest)
admin.site.register(DataLocationQuery)
admin.site.register(ROBDataLocation)
admin.site.register(JSOCDataLocation)
admin.site.register(SAODataLocation)
