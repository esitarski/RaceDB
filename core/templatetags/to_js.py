from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escapejs

import json

register = template.Library()

@register.filter
def to_js(value):
	"""
	To use a python variable in JS, we call json.dumps to serialize as JSON server-side and reconstruct using
	JSON.parse. The serialized string must be escaped appropriately before dumping into the client-side code.
	"""
	# separators is passed to remove whitespace in output
	return mark_safe('JSON.parse("{}")'.format(escapejs(json.dumps(value, separators=(',', ':')))))
