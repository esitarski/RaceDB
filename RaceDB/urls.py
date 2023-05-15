from django.urls import include, path, re_path
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.http.response import HttpResponsePermanentRedirect

from django.contrib import admin

from core import urls as core_urls

# Redirect uses to the main page
def redirect_view(request):
	response = redirect('/RaceDB/')
	return response

admin.autodiscover()

urlpatterns = [
	re_path(r'^[Rr][Aa][Cc][Ee][Dd][Bb]/', include(core_urls)),
	re_path(r'^[Rr]esults/', lambda request: HttpResponsePermanentRedirect('/RaceDB/Hub/')),
	re_path(r'^[Hh]ub/', lambda request: HttpResponsePermanentRedirect('/RaceDB/Hub/')),
	#re_path(r'^admin/', admin.site.urls),
    path('', redirect_view),
]
