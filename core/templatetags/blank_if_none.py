from django import template

register = template.Library()

@register.filter
def blank_if_none( value ):
	return value if value is not None else ''
