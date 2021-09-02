from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def format_time_no_decimals( value ):
	if not value:
		return mark_safe('')
	try:
		return mark_safe(value.format_no_decimals())
	except AttributeError:
		return mark_safe('')
