from django import template
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def format_time_no_decimals( value ):
	try:
		return mark_safe(value.format_no_decimals())
	except AttributeError:
		return mark_safe(u'')
