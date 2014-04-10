from django.conf.urls import patterns, url

from PMD import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index')
)
