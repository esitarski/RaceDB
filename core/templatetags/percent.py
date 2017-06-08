from django import template

register = template.Library()
from django.template.defaultfilters import floatformat

@register.filter
def percent(value, decimals=1):
	if value is None:
		return None
	return floatformat(value * 100.0, decimals) + '%' 