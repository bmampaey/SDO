from django.conf.urls import patterns, url, include

from DRMS import views

from DRMS.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.data_series_list, name='data_series_list'),
	url(r'^(?P<data_series>\w+\.\w+)/$', views.data_series, name='data_series'),
	url(r'^(?P<data_series>\w+\.\w+)/(?P<recnum>\d+)/$', views.recnum, name='recnum'),
	(r'^api/', include(v1_api.urls)),
)
