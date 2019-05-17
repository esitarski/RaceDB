import six
from django import template
register = template.Library()

def non_empty( v ):
	if isinstance(v, six.integer_types) or isinstance(v, float):
		return True
	if isinstance(v, six.string_types):
		return v
	return True

@register.simple_tag
def non_empty_list(*args, **kwargs):
	sep = kwargs.pop('sep', u', ')
	return sep.join( a for a in args if non_empty(a) )
