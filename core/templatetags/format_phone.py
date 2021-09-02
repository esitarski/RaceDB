from django import template

register = template.Library()

@register.filter
def format_phone( value ):
	phone = '{}'.format( value )
	if len(phone) == len('AAA333NNNN') and phone.isdigit():
		return '({}) {}-{}'.format(phone[:3], phone[3:6], phone[6:])
	return phone
