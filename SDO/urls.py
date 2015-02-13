from django.conf.urls import patterns, include, url

from django.contrib import admin, auth
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('account.urls', namespace="account")),
    url(r'^DRMS/', include('DRMS.urls', namespace="DRMS")),
    url(r'^PMD/', include('PMD.urls', namespace="PMD")),
    url(r'^wizard/', include('wizard.urls', namespace="wizard")),
)

# Only when debugging
from django.conf import settings
if settings.DEBUG:
	from django.conf.urls.static import static
	urlpatterns += static(settings.DATA_URL, document_root=settings.DATA_ROOT)
