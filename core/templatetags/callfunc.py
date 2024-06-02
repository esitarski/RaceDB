from django import template
register = template.Library()

@register.simple_tag( takes_context=True )
def callfunc(context, func, arg):
	return context[func]( arg )
