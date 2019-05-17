import os
import re
import sys
import six
import math
import string
import urllib
import datetime
import unicodedata

def uniquify(seq, idfun=None):  
	# order preserving 
	if idfun is None:
		idfun = lambda x: x
	seen = set()
	result = [] 
	for item in seq: 
		marker = idfun(item) 
		if marker not in seen:
			seen.add( marker )
			result.append(item) 
	return result

def format_time_gap( secs, highPrecision=False, separateWithQuotes=True, forceHours=False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = (secs % 60) + f
	if highPrecision:
		secStr = '{:05.2f}'.format( secs )
	else:
		secStr = '{:02d}'.format( int(secs) )	# Truncate fractional seconds.
	if secStr == '60' or secStr == '60.00':
		secStr = '00.00' if highPrecision else '00'
		minutes += 1
		if minutes == 60:
			minutes = 0
			hours += 1
	
	if separateWithQuotes:
		if forceHours or hours > 0:
			return "{}{}h{}'{}\"".format(sign, hours, minutes, secStr)
		else:
			return "{}{}'{}\"".format(sign, minutes, secStr)
	else:
		if forceHours or hours > 0:
			return "{}{}:{:02d}:{}".format(sign, hours, minutes, secStr)
		else:
			return "{}{:02d}:{}".format(sign, minutes, secStr)


def format_time( secs, highPrecision=False, forceHours=False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = (secs % 60) + f
	if highPrecision:
		secStr = '{:05.2f}'.format( secs )
	else:
		secStr = '{:02d}'.format( int(secs) )	# Truncate fractional seconds.
	if secStr == '60' or secStr == '60.00':
		secStr = '00.00' if highPrecision else '00'
		minutes += 1
		if minutes == 60:
			minutes = 0
			hours += 1
	
	if forceHours or hours > 0:
		return "{}{}:{:02d}:{}".format(sign, hours, minutes, secStr)
	else:
		return "{}{:02d}:{}".format(sign, minutes, secStr)

def removeDiacritic( s ):
	'''
	Accept a unicode string, and return a normal string
	without any diacritical marks.
	'''
	return unicodedata.normalize('NFKD', u'{}'.format(s)).encode('ASCII', 'ignore').decode()
	
def safe_print( *args ):
	print ( removeDiacritic( u' '.join(u'{}'.format(a) for a in args) ) )

def cleanExcelSheetName( s ):
	return re.sub( '[\[\]\:\*\?\/\\\]', '-', removeDiacritic(s) )[:31]

reInvalidFilenameChars = re.compile( '[^-_.() a-zA-Z0-9]' )
def cleanFileName( filename ):
	cleanedFilename = removeDiacritic( filename ).replace( '/', '_' )
	return reInvalidFilenameChars.sub( '', cleanedFilename )
	
def toUnicode( s ):
	if isinstance( s, bytes ):			
		encodings = (
			'utf-8', 'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4', 'iso-8859-5',
			'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'iso-8859-10', 'iso-8859-11',
			'iso-8859-13', 'iso-8859-14', 'iso-8859-15',
		)
		for encoding in encodings:
			try:
				return s.decode(encoding)
			except:
				pass
		return s.decode('utf-8', 'ignore')
	
	return u'{}'.format(s)

def getHeaderFields( fields ):
	fields = [removeDiacritic(v) for v in fields]
	fields_new = []
	for i, f in enumerate(fields):
		try:
			f_new = f.encode('ascii')
		except:
			f_new = 'field_name_created_in_col_{}'.format(i)
		fields_new.append( f_new )
	fields = fields_new
	fields = [v.replace('-','_').replace('#','').strip().replace('4', 'four').replace(' ','_') for v in fields]
	fields = [v.strip().lower() for v in fields]
	fields = ['valid_field_name_created_in_col_{}'.format(i) if not f else f for i, f in enumerate(fields)]
	return fields

reSep = re.compile( u'[:;,-/. \t]+' )
def normalizeSeparators( s ):
	return reSep.sub( u' ', s )

def normalizeSearch( s ):
	return normalizeSeparators(removeDiacritic(s.strip())).lower()
	
def matchSearchFields( search, field ):
	if isinstance(search, six.string_types):
		search = normalizeSearch( search ).split()
	field = removeDiacritic( field.strip() ).lower()
	return all( s in field for s in search )
	
escChars = set( r".^$*+?()[{\|" )
def matchSearchToRegEx( search ):
	if isinstance(search, six.string_types):
		search = normalizeSearch( search ).split()
	return re.compile( u''.join([
		u'^',
		u''.join( u'(?=.*{})'.format(u''.join(u'\\{}'.format(c) if c in escChars else c for c in s) for s in search)),
		u'.*$'])
	)

def get_search_text( fields ):
	if not isinstance(fields, list):
		fields = [fields]
	
	return removeDiacritic(
		reSep.sub(
			u' ',
			u' '.join(u'"{}"'.format(f) for f in fields if f)
		).lower()
	)

HexChars = set( '0123456789ABCDEFabcef' )
def allHex( tag ):
	return all( c in HexChars for c in tag.strip() )

def gender_from_str( s ):
	return 1 if s.lower().strip()[:1] in 'wf' else 0

#---------------------------------------------------------------------------------------

reCap = re.compile( '[a-z0-9][A-Z]' )
def splitCapWords( word ):
	while 1:
		m = reCap.search( word )
		if not m:
			break
		i = m.start(0) + 1
		word = word[:i] + ' ' + word[i:]
	return word

reRFID = re.compile( 'RFID', re.IGNORECASE )
class Breadcrumb( object ):
	def __init__( self, name, url ):
		if not url.endswith( '/' ):
			url += '/'
		while url.endswith( '//' ):
			url = url[:-1]
		self.name = reRFID.sub('RFID', name)
		self.url = url

reNum = re.compile( '^[0123456789,]+$' )
class Breadcrumbs( object ):
	def __init__( self, pathIn ):
		self.breadcrumbs = []
		try:
			path = pathIn[:pathIn.index('?')]
		except ValueError:
			path = pathIn
		
		components = path.split( '/' )
		if not components:
			return
			
		if not components[-1]:
			components = components[:-1]
			
		breadcrumbs = []
		i = 1
		while i < len(components):
			j = i + 1
			#
			# Strip numeric arguments to we show the logical path only.
			#
			while j < len(components) and reNum.match( components[j] ):
				j += 1
			breadcrumbs.append( Breadcrumb(splitCapWords(components[i]), '/'.join(components[:j]) ) )
			i = j

		#self.breadcrumbs = breadcrumbs[1:]
		self.breadcrumbs = breadcrumbs
	
	@property
	def title( self ):
		return self.breadcrumbs[-1].name
		
	def pop( self, n = 1 ):
		try:
			return self.breadcrumbs[-1-n].url
		except IndexError:
			return ''
	
	@property
	def url( self ):
		return self.pop(0)
	
	@property
	def cancelUrl( self ):
		return self.pop(1)
	
	@property
	def popUrl( self ):
		return self.pop(1)
	
	@property
	def pop2Url( self ):
		return self.pop(2)
	
	@property
	def pop3Url( self ):
		return self.pop(3)

def popUrl( url ):
	return Breadcrumbs(url).popUrl
	
def pop2Url( url ):
	return Breadcrumbs(url).pop2Url
	
def pop3Url( url ):
	return Breadcrumbs(url).pop3Url
	
def cancelUrl( url ):
	return Breadcrumbs(url).cancelUrl

if __name__ == '__main__':
	print ( uniquify([4,4,4,4,3,3,3,2,2,1]) )
