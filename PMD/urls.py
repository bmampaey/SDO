from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^login$', views.login, name='login'),
	url(r'^result_table/(?P<data_series>\w+)$', views.result_table, name='result_table'),
	url(r'^thumbnail/(?P<data_series>\w+)/(?P<recnum>\d+)$', views.thumbnail, name='thumbnail'),
	url(r'^download/(?P<data_series>\w+)/(?P<recnum>\d+)$', views.download, name='download'),
	url(r'^bring_online$', views.bring_online, name='bring_online'),
	url(r'^api/', include(v1_api.urls)),
)
