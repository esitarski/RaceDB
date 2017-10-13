from django import template
register = template.Library()

@register.filter
def call(obj, methodName):
	method = getattr(obj, methodName)
	if hasattr(obj, '__callArg'):
		ret = method(*obj.__callArg)
		del obj.__callArg
		return ret
	return method()
	
@register.filter
def args(obj, arg):
	if hasattr(obj, '__callArg'):
		obj.__callArg.append( arg )
	else:
		obj.__callArg = [arg]
	return obj
