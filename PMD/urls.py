from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^log_in_user$', views.log_in_user, name='log_in_user'),
	url(r'^search_result_table/(?P<data_series_name>\w+)$', views.search_result_table, name='search_result_table'),
	url(r'^preview_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.preview_data, name='preview_data'),
	url(r'^download_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.download_data, name='download_data'),
	url(r'^search_result_action/(?P<action_type>\w+)/(?P<data_series_name>\w+)$', views.search_result_action, name='search_result_action'),
	url(r'^export_data_request_table$', views.export_data_request_table, name='export_data_request_table'),
	url(r'^delete_export_data_request/(?P<request_id>\d+)$', views.delete_export_data_request, name='delete_export_data_request'),
	url(r'^api/', include(v1_api.urls)),
)
