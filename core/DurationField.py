from django.db.models.fields import FloatField
from django.db import models
from django.core.exceptions import ValidationError

from django.forms.fields import CharField
from django.forms.utils import ValidationError as FormValidationError

import re
import datetime
import math

reDuration = re.compile( r'^[+-]?([0-9]*:)*[0-9]+\.?[0-9]*$' )

def format_seconds( secs ):
	if secs < 0:
		sgnStr = '-'
		secs = -secs
	else:
		sgnStr = ''
	fraction, seconds = math.modf( secs )
	seconds = int(seconds)
	hours = seconds // (60*60)
	minutes = (seconds // 60) % 60
	seconds %= 60
	if fraction > 0.000001:
		secStr = '{:06.3f}'.format( seconds + fraction )
	else:
		secStr = '{:02d}'.format( seconds )
		
	if hours:
		return '{}{}:{:02d}:{}'.format(sgnStr, hours, minutes, secStr )
	return '{}{}:{}'.format(sgnStr, minutes, secStr )

class formatted_timedelta(datetime.timedelta):
	def __repr__( self ):
		return format_seconds( self.total_seconds() )

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
			raise FormValidationError('Must be in format [-]HH:MM:SS.ddd')
		return value

#------------------------------------------------------------------------------------

class DurationField( FloatField ):

	description = "Floating point representation of timedelta."

	def __init__( self, *args, **kwargs ):
		super( DurationField, self ).__init__( *args, **kwargs )
	
	def to_python( self, value ):
		if value is None:
			return None
			
		if isinstance(value, formatted_timedelta):
			return value
			
		if isinstance(value, datetime.timedelta):
			return formatted_timedelta( seconds=value.total_seconds() )
			
		if isinstance(value, (int, long, float)):
			return formatted_timedelta( seconds=value )
			
		if isinstance(value, datetime.time):
			return formatted_timedelta( seconds = value.hour * 60.0*60.0 + value.minute * 60.0 +
									   value.second + value.microsecond / 1000000.0 )
			
		try:
			# Try parsing the value as a string.
			
			value = value.strip()
			sgn = 1
			if value.startswith('-'):
				sgn = -1
				value = value[1:]
			elif value.startswith('+'):
				value = value[1:]
			
			secs = 0.0
			for f in value.split(':'):
				try:
					secs = secs * 60.0 + float(f)
				except:
					secs *= 60.0
			return formatted_timedelta( seconds = sgn * secs )
		except Exception as e:
			raise ValidationError('Unable to convert {} to time ({}).'.format(value, e) )
		return value
	
	def from_db_value( self, value, expression, connection, context ):
			if value is None:
				return value
			return formatted_timedelta( seconds = value )
	
	def get_db_prep_value(self, value, connection, prepared=False):
		try:
			return value.total_seconds()
		except AttributeError:
			return None
		
	def value_to_string( self, instance ):
		td = getattr(instance, self.name)
		if td:
			return format_seconds( td.total_seconds() )
		return None
		
	def formfield( self, form_class=DurationFormField, **kwargs ):
		defaults = {"help_text": "[-]HH:MM:SS.ddd"}
		defaults.update(kwargs)
		return form_class(**defaults)
