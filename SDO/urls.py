from django.conf.urls import patterns, include, url

from django.contrib import admin, auth
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SDO.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('accounts.urls', namespace="accounts")),
    url(r'^DRMS/', include('DRMS.urls', namespace="DRMS")),
    url(r'^PMD/', include('PMD.urls', namespace="PMD")),
)

# TODO remove in production
from django.conf.urls.static import static
from django.conf import settings
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
