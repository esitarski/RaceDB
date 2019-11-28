from django.conf.urls import include, re_path
from django.urls import path
from django.shortcuts import redirect

from django.contrib import admin

from core import urls as core_urls

# Redirect uses to the main page
def redirect_view(request):
	response = redirect('/RaceDB/')
	return response

admin.autodiscover()

urlpatterns = [
	re_path(r'^[Rr][Aa][Cc][Ee][Dd][Bb]/', include(core_urls)),
	re_path(r'^admin/', admin.site.urls),
    path('', redirect_view),
]
