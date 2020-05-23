from django import template
from django.utils import dateformat
from core.models import SystemInfo
register = template.Library()

@register.simple_tag(takes_context=True)
def date_short_jquery(context):
	return SystemInfo.get_formats().date_short_jquery

@register.simple_tag(takes_context=True)
def date_hhmmss_jquery(context):
	return SystemInfo.get_formats().date_hhmmss_jquery

@register.simple_tag(takes_context=True)
def date_hhmm_jquery(context):
	return SystemInfo.get_formats().date_hhmm_jquery

@register.filter(expects_localtime=True)
def date_short( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_short)

@register.filter(expects_localtime=True)
def date_hhmmss( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_hhmmss)

@register.filter(expects_localtime=True)
def date_hhmm( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_hhmm)

@register.filter(expects_localtime=True)
def date_Md_hhmm( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_Md_hhmm)

@register.filter(expects_localtime=True)
def date_year_Md_hhmm( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_year_Md_hhmm)

@register.filter(expects_localtime=True)
def date_year_Md( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().date_year_Md)

@register.filter(expects_localtime=True)
def time_hhmmss( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().time_hhmmss)

@register.filter(expects_localtime=True)
def time_hhmm( value ):
	return dateformat.DateFormat( value ).format(SystemInfo.get_formats().time_hhmm)
