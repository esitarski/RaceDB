from django import template
register = template.Library()

@register.filter
def formatattr ( value ):
	if value is None:
		return ''
	
	if isinstance( value, float ):
		if value > 0.0:
			return '{:.2f}'.format( value )
		else:
			return ''
	if isinstance( value, int ) and value == 0:
		return ''
		
	return str(value)
