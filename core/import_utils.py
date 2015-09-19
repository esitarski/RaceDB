import datetime
import time
from xlrd import xldate_as_tuple
from utils import toUnicode, removeDiacritic, gender_from_str

datemode = None

today = datetime.date.today()
earliest_year = (today - datetime.timedelta( days=106*365 )).year
latest_year = (today - datetime.timedelta( days=7*365 )).year

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
		print yy, mm, dd
		raise e
		
def set_attributes( obj, attributes, accept_empty_values=False ):
	changed = False
	for key, value in attributes.iteritems():
		if (accept_empty_values or value) and getattr(obj, key) != value:
			setattr(obj, key, value)
			changed = True
	return changed
	
def to_int_str( v ):
	if v is None:
		return None
	try:
		return unicode(long(v))
	except:
		pass
	return unicode(v)
		
def to_str( v ):
	if v is None:
		return v
	return toUnicode(v).strip()
	
def to_bool( v ):
	if v is None:
		return None
	s = unicode(v).strip()
	return s[:1] in u'YyTt1'

def to_int( v ):
	if v is None:
		return None
	try:
		return int(v)
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

