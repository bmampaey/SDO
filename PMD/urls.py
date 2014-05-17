from django.conf.urls import patterns, url, include

from PMD import views

from PMD.api.api import v1_api

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^search_data$', views.search_data, name='search_data'),
	url(r'^bring_online$', views.bring_online, name='bring_online'),
	(r'^api/', include(v1_api.urls)),
)
