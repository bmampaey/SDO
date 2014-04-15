from django.contrib import admin

# Register your models here.
from PMD.models import DataSite, DataSeries, ROBDataLocation, JSOCDataLocation, SAODataLocation
admin.site.register(DataSite)
admin.site.register(DataSeries)
admin.site.register(ROBDataLocation)
admin.site.register(JSOCDataLocation)
admin.site.register(SAODataLocation)
