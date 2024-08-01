formatMap = {
	'd': 'DD',
	'D': 'ddd',
	'j': 'D',
	'l': 'dddd',
	'N': 'E',
	'w': 'd',
	'W': 'W',
	'F': 'MMMM',
	'm': 'MM',
	'M': 'MMM',
	'n': 'M',
	'o': 'GGGG',
	'Y': 'YYYY',
	'y': 'YY',
	'a': 'a',
	'A': 'A',
	'g': 'h',
	'G': 'H',
	'h': 'hh',
	'H': 'HH',
	'i': 'mm',
	's': 'ss',
	'O': 'ZZ',
	'P': 'Z',
	'c': 'YYYY-MM-DD[T]HH:mm:ssZ',
	'r': 'ddd, DD MMM YYYY HH:mm:ss ZZ',
	'U': 'X',
}

def php_moment( fmt ):
	#
	# PHP => moment.js
	#
	# http://www.php.net/manual/en/function.date.php
	# http://momentjs.com/docs/#/displaying/format/
	#	
	return ''.join( formatMap.get(c, c) for c in fmt )
