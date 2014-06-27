from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^login$', views.login, name='login'),
	url(r'^result_table/(?P<data_series_name>\w+)$', views.result_table, name='result_table'),
	url(r'^request_table$', views.request_table, name='request_table'),
	url(r'^preview/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.preview, name='preview'),
	url(r'^download/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.download, name='download'),
	url(r'^result_action/(?P<action_type>\w+)/(?P<data_series_name>\w+)$', views.result_action, name='result_action'),
	url(r'^delete_export_request/(?P<request_id>\d+)$', views.delete_export_request, name='delete_export_request'),
	url(r'^api/', include(v1_api.urls)),
)
