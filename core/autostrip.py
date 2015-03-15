from django import forms

def autostrip(cls):
	fields = [(key, value) for key, value in cls.base_fields.iteritems() if isinstance(value, forms.CharField)]
	for field_name, field_object in fields:
		def get_clean_func(original_clean):
			return lambda value: original_clean(value and value.strip())
		clean_func = get_clean_func(getattr(field_object, 'clean'))
		setattr(field_object, 'clean', clean_func)
	return cls