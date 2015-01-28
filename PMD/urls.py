from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^login$', views.login, name='login'),
	url(r'^logout', 'django.contrib.auth.views.logout', name='logout'),
	url(r'^search_result_table/(?P<data_series_name>\w+)$', views.search_result_table, name='search_result_table'),
	url(r'^preview_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.preview_data, name='preview_data'),
	url(r'^download_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)(/.*)?$', views.download_data, name='download_data'),
	url(r'^search_result_action/(?P<action_type>\w+)/(?P<data_series_name>\w+)$', views.search_result_action, name='search_result_action'),
	url(r'^user_request_table/(?P<request_type>\w+)$', views.user_request_table, name='user_request_table'),
	url(r'^delete_user_request/(?P<request_type>\w+)/(?P<request_id>\d+)$', views.delete_user_request, name='delete_user_request'),
	url(r'^api/', include(v1_api.urls)),
)
