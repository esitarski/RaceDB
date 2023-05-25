import datetime
from django import template
register = template.Library()

@register.filter
def isnumber ( value ):
	return isinstance( value, (float, int, datetime.timedelta) )
