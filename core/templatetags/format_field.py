from django import template

register = template.Library()

@register.filter
def format_field( value ):
	field = '{}'.format( value )
	if not field:
		return ''
	
	parts = field.split( '_' )
	no_caps = {
		'a', 'and', 'as', 'at', 'by', 'down', 'for', 'from', 'if',
		'in', 'into', 'like', 'near', 'nor', 'of', 'off', 'on', 'once',
		'onto', 'or', 'over', 'past', 'so',
		'than', 'that', 'to', 'upon', 'when', 'with', 'yet',
	}
	return parts[0].capitalize() + ' ' + ' '.join( p if p in no_caps else p.capitalize() for p in parts[1:] )
