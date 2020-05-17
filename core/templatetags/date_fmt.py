from django import template
from django.utils import dateformat
import core.date_transform as dtrans
register = template.Library()

@register.simple_tag
def date_short_jquery():
	return dtrans.date_short_jquery

@register.simple_tag
def date_hhmmss_jquery():
	return dtrans.date_hhmmss_jquery

@register.simple_tag
def date_hhmm_jquery():
	return dtrans.date_hhmm_jquery

@register.filter(expects_localtime=True)
def date_short( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_short)

@register.filter(expects_localtime=True)
def date_hhmmss( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_hhmmss)

@register.filter(expects_localtime=True)
def date_hhmm( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_hhmm)

@register.filter(expects_localtime=True)
def date_Md_hhmm( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_Md_hhmm)

@register.filter(expects_localtime=True)
def date_year_Md_hhmm( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_year_Md_hhmm)

@register.filter(expects_localtime=True)
def date_year_Md( value ):
	return dateformat.DateFormat( value ).format(dtrans.date_year_Md)

@register.filter(expects_localtime=True)
def time_hhmmss( value ):
	return dateformat.DateFormat( value ).format(dtrans.time_hhmmss)

@register.filter(expects_localtime=True)
def time_hhmm( value ):
	return dateformat.DateFormat( value ).format(dtrans.time_hhmm)
