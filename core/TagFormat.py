import re

reTemplate = re.compile( u'#+' )
validChars = set( u'0123456789ABCDEF#' )

def getValidTagFormatStr( template ):
	template = u''.join( c for c in template if c in validChars )
	return template

def getTagFormatStr( template ):
	template = getValidTagFormatStr( template )
	if u'#' not in template:
		template = u'#' + template
	while 1:
		m = reTemplate.search( template )
		if not m:
			break
		template = template[:m.start(0)] + u'{{n:0{}d}}'.format(len(m.group(0))) + template[m.end(0):]
	return template