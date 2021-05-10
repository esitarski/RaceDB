from django import template
register = template.Library()

def non_empty( v ):
	if isinstance(v, (int, float) ):
		return True
	if isinstance(v, str):
		return v
	return True

@register.simple_tag
def non_empty_list(*args, **kwargs):
	sep = kwargs.pop('sep', ', ')
	return sep.join( a for a in args if non_empty(a) )
