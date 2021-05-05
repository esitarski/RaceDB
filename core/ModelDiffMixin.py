from django.forms.models import model_to_dict

class ModelDiffMixin:
	"""
	A model mixin that tracks model fields' values and provide some useful api
	to know what fields have been changed.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__initial = self._dict

	@property
	def diff(self):
		d1 = self.__initial
		d2 = self._dict
		diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
		return dict(diffs)

	@property
	def has_changed(self):
		return bool(self.diff)

	@property
	def changed_fields(self):
		return self.diff.keys()

	def get_field_diff(self, field_name):
		"""
		Returns a diff for field if it's changed and None otherwise.
		"""
		return self.diff.get(field_name, None)

	def save(self, *args, **kwargs):
		"""
		Saves model and set initial state.
		"""
		super().save(*args, **kwargs)
		self.__initial = self._dict

	@property
	def _dict(self):
		return model_to_dict(self, fields=[field.name for field in self._meta.fields])
