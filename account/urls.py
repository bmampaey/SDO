from django.conf.urls import patterns, url
from account import views

urlpatterns = patterns('',
	url(r'login$', views.EmailLoginView.as_view(), name='login'),
	url(r'logout$', 'django.contrib.auth.views.logout', name='logout'),
)

