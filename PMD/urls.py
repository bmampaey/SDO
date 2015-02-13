from django.conf.urls import patterns, url

from PMD import views

urlpatterns = patterns('',
	url(r'^preview_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)$', views.preview_data, name='preview_data'),
	url(r'^download_data/(?P<data_series_name>\w+)/(?P<recnum>\d+)(/.*)?$', views.download_data, name='download_data'),
)
