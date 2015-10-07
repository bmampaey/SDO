from django.conf.urls import patterns, url

from vso import views

urlpatterns = patterns('',
	url(r'^drms_export.cgi$', views.drms_export, name='drms_export'),
)
