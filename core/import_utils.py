import re
import six
import time
import datetime
from xlrd import xldate_as_tuple
from django.utils import timezone
from .utils import toUnicode, removeDiacritic, gender_from_str

datemode = None

dNow = timezone.localtime(timezone.now()).date()
earliest_year = (dNow - datetime.timedelta( days=106*365 )).year
latest_year = (dNow - datetime.timedelta( days=7*365 )).year

invalid_date_of_birth = datetime.date(1900, 1, 1)
def date_from_value( s ):
	if isinstance(s, datetime.date):
		return s
	if isinstance(s, datetime.datetime):
		return s.date()
	
	if isinstance(s, (float, int)):
		return datetime.date( *(xldate_as_tuple(s, datemode)[:3]) )
		
	try:
		s = s.replace('-', '/')
	except:
		pass
	
	# Start with month, day, year format.
	try:
		mm, dd, yy = [int(v.strip()) for v in s.split('/')]
	except:
		return invalid_date_of_birth
	
	if mm > 1900:
		# Switch to yy, mm, dd format.
		yy, mm, dd = mm, dd, yy
	
	# Correct for 2-digit year.
	for century in [0, 1900, 2000, 2100]:
		if earliest_year <= yy + century <= latest_year:
			yy += century
			break
	
	# Check if day and month are reversed.
	if mm > 12:
		dd, mm = mm, dd
		
	assert 1900 <= yy
		
	try:
		return datetime.date( year=yy, month=mm, day=dd )
	except Exception as e:
		print ( yy, mm, dd )
		raise e
		
def set_attributes( obj, attributes, accept_empty_values=False ):
	changed = False
	for key, value in attributes.items():
		if (accept_empty_values or value) and getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def set_attributes_changed( obj, attributes, accept_empty_values=False ):
	changed = []
	for key, value in attributes.items():
		if (accept_empty_values or value) and getattr(obj, key) != value:
			setattr(obj, key, value)
			changed.append( (key, value) )
	return changed

reNoSpace = re.compile(u'\u200B', flags=re.UNICODE)
reAllSpace = re.compile(r'\s', flags=re.UNICODE)
def fix_spaces( v ):
	if v and isinstance(v, six.string_types):
		v = reNoSpace.sub( u'', v )		# Replace zero space with nothing.
		v = reAllSpace.sub( u' ', v )	# Replace alternate spaces with a regular space.
		v = v.strip()
	return v
	
def to_int_str( v ):
	if v is None:
		return None
	fix_spaces( v )
	try:
		return u'{}'.format(int(v))
	except:
		pass
	return toUnicode(v)

reUCIID = re.compile( r'[^\d]' )
def to_uci_id( v ):
	if v is None:
		return None
	try:
		v = u'{}'.format(int(v))
	except:
		v = toUnicode(v)
	return reUCIID.sub( u'', v )
		
def to_str( v ):
	if v is None:
		return v
	return fix_spaces(toUnicode(v)).strip()
	
def to_phone( v ):
	if v is None:
		return v
	v = to_int_str( v )
	return v[:-2] if v.endswith(u'.0') else v
	
def to_bool( v ):
	if v is None:
		return None
	s = fix_spaces(u'{}'.format(v)).strip()
	return s[:1] in u'YyTt1' if s else None

def to_int( v ):
	if v is None:
		return None
	v = fix_spaces( v )
	try:
		return int(v)
	except:
		return None

def to_float( v ):
	if v is None:
		return None
	v = fix_spaces( v )
	try:
		return float(v)
	except:
		return None

def to_tag( v ):
	return None if v is None else to_int_str(v).upper()

def get_key( d, keys, default_value ):
	for k in keys:
		k = k.lower()
		if k in d:
			return d[k]
	return default_value

def date_of_birth_from_age( age, today=None ):
	if age is None:
		return None
	if isinstance(age, datetime.date):
		return age
	if isinstance(age, datetime.datetime):
		return age.date()
	try:
		age = int(age)
	except:
		return None
	if 1900 <= age:
		return datetime.date( age, 1, 1 )
	if not today:
		today = datetime.date.today()
	return datetime.date( today.year - age, 1, 1 )
