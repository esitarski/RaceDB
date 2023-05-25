from django import template
register = template.Library()

@register.filter
def getattr (obj, args):
	""" Try to get an attribute from an object.

	Example: {% if block|getattr:"editable,True" %}

	Beware that the default is always a string, if you want this
	to return False, pass an empty second argument:
	{% if block|getattr:"editable," %}
	"""
	args = args.split(',')
	if len(args) == 1:
		(attribute, default) = [args[0], ''] 
	else:
		(attribute, default) = args
	try:
		return obj.__getattribute__(attribute)
	except AttributeError:
		 return  obj.__dict__.get(attribute, default)
	except:
		return default
