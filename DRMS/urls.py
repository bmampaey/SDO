from django.conf.urls import patterns, url

from DRMS import views

urlpatterns = patterns('',
	url(r'^$', views.data_series_list, name='data_series_list'),
	url(r'^(?P<data_series>\w+\.\w+)/$', views.data_series, name='data_series'),
	url(r'^(?P<data_series>\w+\.\w+)/(?P<recnum>\d+)/$', views.recnum, name='recnum'),
)
