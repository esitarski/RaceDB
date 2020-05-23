class dotdict(dict):
	"""dot.notation access to dictionary attributes"""
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__

php_to_jquery = {
	'y': 'yy',
	'Y': 'yyyy',
	'd': 'dd',
	'm': 'mm',
	
	'a': 'p',
	'A': 'P',
	's': 'ss',
	'i': 'ii',
	'h': 'HH',	# 12 hour representation
	'H': 'hh',	# 24 hour representation
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

class FormatCache( dotdict ):
	def __init__( self, system_info ):
		super().__init__()
		
		# Basic formats.
		self.date_short = system_info.date_short
		self.date_Md = system_info.date_Md
		self.time_hhmmss = system_info.time_hhmmss
		
		# Derived formats.
		self.time_hhmm = self.time_hhmmss.replace( ':s', '' )
		self.date_year_Md = ('Y ' + self.date_Md) if self.date_Md.startswith('M') else (self.date_Md + ' Y')
		self.date_Md_hhmm = self.date_Md + ' ' + self.time_hhmm
		self.date_hhmmss = self.date_short + ' ' + self.time_hhmmss
		self.date_hhmm = self.date_short + ' ' + self.time_hhmm
		self.date_year_Md_hhmm = self.date_year_Md + ' ' + self.time_hhmm
		
		# Translated formats.
		for v in ('date_short', 'date_hhmmss', 'date_hhmm', 'date_year_Md', 'date_year_Md_hhmm', 'time_hhmmss', 'time_hhmm'):
			self[v + '_jquery'] = translate(self[v], php_to_jquery)
			self[v + '_python'] = translate(self[v], php_to_python)

		# for k,v in self.items(): print( k, '=', v )


