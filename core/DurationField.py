from django.db.models.fields import FloatField
from django.db import models
from django.core.exceptions import ValidationError

from django.forms.fields import CharField
from django.forms.util import ValidationError as FormValidationError

import re
import datetime
import math

reDuration = re.compile( r'^[+-]?([0-9]*:)*[0-9]+\.?[0-9]*$' )

class formatted_timedelta(datetime.timedelta):
	def __repr__( self ):
		secs = self.total_seconds()
		if secs < 0:
			sgn = '-'
			secs = -secs
		else:
			sgn = ''
		fract, ss = math.modf( secs )
		ss = int(ss)
		hh = ss // (60*60)
		mm = (ss // 60) % 60
		ss %= 60
		if fract < 0.000001:
			return '%s%d:%02d:%02d' % (sgn, hh, mm, ss)
		else:
			return '%s%d:%02d:%02d.%s' % (sgn, hh, mm, ss, ('%.3f' % fract)[2:])
			
	def __unicode__( self ):
		return unicode(self.__repr__())
		
	def __str__( self ):
		return self.__repr__( self )

class DurationFormField( CharField ):
	def __init__(self, *args, **kwargs):
		self.max_length = 13
		super(DurationFormField, self).__init__(*args, **kwargs)

	def clean(self, value):
		value = super(CharField, self).clean(value)
		value = value.strip()
		if value and not reDuration.match(value):
			raise FormValidationError('Must be in format [-]HH:MM:SS.SSS')
		return value

#------------------------------------------------------------------------------------
		
class DurationField( FloatField ):

	description = "Floating point representation of timedelta."

	__metaclass__ = models.SubfieldBase
	
	def to_python(self, value):
		if value is None:
			return None
			
		if isinstance(value, formatted_timedelta):
			return value
			
		if isinstance(value, datetime.timedelta):
			return formatted_timedelta( seconds = value.total_seconds() )
			
		if isinstance(value, (int, long, float)):
			return formatted_timedelta(seconds=value)
			
		if isinstance(value, datetime.time):
			return formatted_timedelta( seconds = value.hour * 60*60 + value.minute * 60 +
									   value.second + value.microsecond / 1000000.0 )
			
		try:
			secs = 0.0
			value = value.strip()
			
			sgn = 1
			if value:
				if value[0] == '-':
					sgn = -1
					value = value[1:]
				elif value[0] == '+':
					value = value[1:]
				
			for f in value.split(':'):
				try:
					secs = secs * 60.0 + float(f)
				except:
					secs *= 60.0
			return formatted_timedelta( seconds = sgn * secs )
		except Exception as e:
			raise ValidationError('Unable to convert {} to time ({}).'.format(value, e) )
		return value
		
	def get_db_prep_value(self, value, connection, prepared=False):
		try:
			return value.total_seconds()
		except AttributeError:
			return None
		
	def value_to_string(self, instance):
		timedelta = getattr(instance, self.name)
		if timedelta:
			posSecs = timedelta.total_seconds()
			if posSecs < 0.0:
				posSecs = -posSecs
				sgnStr = '-'
			else:
				sgnStr = ''
			fraction, seconds = math.modf( posSecs )
			seconds = int(seconds)
			if fraction:
				return '%s%d:%02d:%02d.%s' % (sgnStr, seconds // (60*60), (seconds // 60) % 60, seconds % 60, ('%.3f' % fraction)[2:] )
			else:
				return '%s%d:%02d:%02d' % (sgnStr, seconds // (60*60), (seconds // 60) % 60, seconds % 60 )
		return None
		
	def formfield(self, form_class=DurationFormField, **kwargs):
		defaults = {"help_text": "[-]HH:MM:SS.SSS"}
		defaults.update(kwargs)
		return form_class(**defaults)
		
#from south.modelsinspector import add_introspection_rules
#add_introspection_rules([], ["^DurationField\."])
