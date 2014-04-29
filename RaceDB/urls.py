from django.conf.urls import patterns, include, url
from django.shortcuts import redirect

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
	'',
	url(r'^(?i)RaceDB/', include('core.urls')),
	url(r'^(?i)admin/', include(admin.site.urls)),
)
