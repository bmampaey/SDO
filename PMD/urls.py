from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^login$', views.login, name='login'),
	url(r'^result_table/(?P<data_series_name>\w+)$', views.result_table, name='result_table'),
	url(r'^preview/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.preview, name='preview'),
	url(r'^download/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.download, name='download'),
	url(r'^download_bundle/(?P<data_series_name>\w+)$', views.download_bundle, name='download_bundle'),
	url(r'^export_data/(?P<data_series_name>\w+)$', views.bring_online, name='export_data'),
	url(r'^export_keywords/(?P<data_series_name>\w+)$', views.export_keywords, name='export_keywords'),
	url(r'^bring_online/(?P<data_series_name>\w+)$', views.bring_online, name='bring_online'),
	url(r'^export_cutout/(?P<data_series_name>\w+)$', views.export_cutout, name='export_cutout'),
	url(r'^api/', include(v1_api.urls)),
)
