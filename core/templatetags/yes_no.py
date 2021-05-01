from django import template
from django.utils.translation import gettext_lazy as _
register = template.Library()

@register.filter
def yes_no( value ):
	return _('Yes') if value else _('No')
