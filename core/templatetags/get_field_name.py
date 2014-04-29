from django import template
register = template.Library()

@register.filter
def get_field_name( instance, field_name ):
	return instance._meta.get_field(field_name).verbose_name
	
@register.filter
def get_field_name_plural( instance, field_name ):
	return instance._meta.get_field(field_name).verbose_name_plural
