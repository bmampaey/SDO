from django.conf.urls import patterns, url

from wizard import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^search_result_table/(?P<data_series_name>\w+)$', views.search_result_table, name='search_result_table'),
	url(r'^search_result_action/(?P<action_type>\w+)/(?P<data_series_name>\w+)$', views.search_result_action, name='search_result_action'),
	url(r'^user_request_table/(?P<request_type>\w+)$', views.user_request_table, name='user_request_table'),
	url(r'^delete_user_request/(?P<request_type>\w+)/(?P<request_id>\d+)$', views.delete_user_request, name='delete_user_request'),
)
