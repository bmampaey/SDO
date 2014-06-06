from django.contrib import admin

# Register your models here.
from PMD.models import GlobalConfig, DataSite, DataSeries, LocalDataLocation, ROBDataLocation, JSOCDataLocation, SAODataLocation
admin.site.register(GlobalConfig)
admin.site.register(DataSite)
admin.site.register(DataSeries)
admin.site.register(LocalDataLocation)
admin.site.register(ROBDataLocation)
admin.site.register(JSOCDataLocation)
admin.site.register(SAODataLocation)
