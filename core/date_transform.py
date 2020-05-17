from django.conf import settings

date_short_default = 'Y-m-d'
date_Md_default = 'M d'
time_hhmmss_default = 'H:i:s'

date_short = getattr( settings, 'RACEDB_DATE_SHORT', date_short_default )
date_Md = getattr( settings, 'RACEDB_DATE_MONTH_DAY', date_Md_default )
time_hhmmss = getattr( settings, 'RACEDB_TIME_HHMMSS', time_hhmmss_default )
time_hhmm = time_hhmmss.replace( ':s', '' )

date_year_Md = ('Y ' + date_Md) if date_Md[0] != 'd' else (date_Md + ' Y')
date_Md_hhmm = date_Md + ' ' + time_hhmm
date_hhmmss = date_short + ' ' + time_hhmmss
date_hhmm = date_short + ' ' + time_hhmm
date_year_Md_hhmm = date_year_Md + ' ' + time_hhmm

# https://docs.google.com/spreadsheets/d/1lPzBlmJVAkN6HUw28wBJmY1SdbSInRIBY0JCmBUDUmk/edit?amp;hl=en_US#gid=0

php_to_jquery = {
	'y': 'yy',
	'Y': 'yyyy',
	'd': 'dd',
	'm': 'mm',
	
	'a': 'a',
	'A': 'A',
	's': 'ss',
	'i': 'ii',
	'h': 'hh',
	'H': 'HH',
}

php_to_python = {
	'y': '%y',
	'Y': '%Y',
	'd': '%d',
	'j': '%d',
	'm': '%m',
	'l': '%a',
	'M': '%b',
	'F': '%B',
	
	'a': '%p',
	'A': '%p',
	's': '%S',
	'i': '%M',
	'h': '%h',
	'H': '%H',
}

def translate( fmt, d ):
	return ''.join( d.get(c, c) for c in fmt )

values = {}
for v in ('date_short', 'date_hhmmss', 'date_hhmm', 'date_year_Md', 'date_year_Md_hhmm', 'time_hhmmss', 'time_hhmm'):
	values[v + '_jquery'] = translate(globals()[v], php_to_jquery)
	values[v + '_python'] = translate(globals()[v], php_to_python)
globals().update( values )

del php_to_jquery
del php_to_python
del values

for k,v in( sorted((k,v) for k, v in globals().items() if any( v in k for v in ('date_', 'time_'))) ):
	print( k, ' = "{}"'.format(v) )
