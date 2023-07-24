from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.http.response import HttpResponsePermanentRedirect

from django.contrib import admin

from core import urls as core_urls

# Redirect uses to the main page
def redirect_view(request):
	response = redirect('/RaceDB/Hub/')
	return response

admin.autodiscover()

urlpatterns = [
	re_path(r'^[Rr][Aa][Cc][Ee][Dd][Bb]/', include(core_urls)),
	re_path(r'^[Rr]esults/', lambda request: HttpResponsePermanentRedirect('/RaceDB/Hub/')),
	re_path(r'^[Hh]ub/', lambda request: HttpResponsePermanentRedirect('/RaceDB/Hub/')),
	#re_path(r'^admin/', admin.site.urls),
    path('', redirect_view),
]

# Set this as a backstop.  In production, configure an alias for the web server (eg. nginx) to get this file directly.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
