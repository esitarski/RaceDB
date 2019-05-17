from django.conf.urls import include, re_path
from django.shortcuts import redirect

from django.contrib import admin

from core import urls as core_urls

admin.autodiscover()

urlpatterns = [
	re_path(r'^RaceDB/', include(core_urls)),
	re_path(r'^admin/', admin.site.urls),
]
