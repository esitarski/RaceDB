from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def format_uci_id( value ):
	uci_id = re.sub( '[^0-9]', '', '{}'.format(value) )
	return mark_safe('&nbsp;'.join( uci_id[i:i+3] for i in range(0, len(uci_id), 3) ) )
