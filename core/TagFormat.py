import re
import utils
from math import log, ceil

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

bytes_from_digits = { n: int(ceil(log(10**n, 256))) for n in xrange(1, 32) }
reNumEnd = re.compile( '[0-9]+$' )
def getTagFromLicense( license, tag_from_license_id=0 ):
	license = utils.removeDiacritic(license.strip())
	result = reNumEnd.search( license )
	if result:
		text = license[:result.start()]
		text_count = len(text)
		num = license[result.start():result.end()]
		num_count = len(num)
	else:
		text = license
		text_count = len(text)
		num = '0'
		num_count = 0
		
	if num_count:
		return '{tag_from_license_id:02X}{text_count:X}{num_count:X}{text_hex}{num:0{byte_count}X}'.format(
			tag_from_license_id=255-tag_from_license_id,
			text_count = text_count,
			num_count = num_count,
			text_hex=''.join( '{:02X}'.format(ord(c)) for c in text ),
			num=int(num),
			byte_count=bytes_from_digits[num_count],
		)
	else:
		return '{tag_from_license_id:02X}{text_count:X}0{text_hex}'.format(
			tag_from_license_id=255-tag_from_license_id,
			text_count = text_count,
			text_hex=''.join( '{:02X}'.format(ord(c)) for c in text ),
		)

def getLicenseFromTag( tag, tag_from_license_id=0 ):
	try:
		tflid = int( tag[0:2], 16 )
	except ValueError:
		return None
	
	if tflid != 255-tag_from_license_id:
		return None

	prefix_count = 2
	text_count = int( tag[prefix_count], 16 )
	num_count = int( tag[prefix_count+1], 16 )
	
	prefix_count += 2
	text = ''.join( chr(int(tag[i:i+2], 16)) for i in xrange(prefix_count, prefix_count+text_count*2, 2) )
	if not num_count:
		return text
	
	prefix_count += text_count*2
	
	byte_count = bytes_from_digits[num_count]
	num = int( tag[prefix_count:prefix_count+byte_count*2], 16 )
	return text + str(num).rjust( num_count, '0' )

if __name__ == '__main__':
	for license in ('CAN19650922', 'ON0123', 'BC0567', 'SK9999', '123567', 'ALLTEXT', ''):
		tag = getTagFromLicense( license )
		license_new = getLicenseFromTag( tag )
		print '"{}" {} "{}"'.format(license, tag, license_new)
		assert license == license_new