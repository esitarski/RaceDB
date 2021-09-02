import re
from math import log, ceil
from . import utils

reTemplate = re.compile( '#+' )
validChars = set( '0123456789ABCDEF#' )

def getValidTagFormatStr( template ):
	template = ''.join( c for c in template if c in validChars )
	return template

def getTagFormatStr( template ):
	template = getValidTagFormatStr( template )
	if '#' not in template:
		template = '#' + template
	while 1:
		m = reTemplate.search( template )
		if not m:
			break
		template = template[:m.start(0)] + '{{n:0{}d}}'.format(len(m.group(0))) + template[m.end(0):]
	return template

bytes_from_digits = tuple( int(ceil(log(10**n, 256))) for n in range(0, 16) )
reNumEnd = re.compile( '[0-9]+$' )
def getTagFromLicense( license, tag_from_license_id=0 ):
	license = utils.removeDiacritic(license.strip().upper())
	
	for prefix in ('_XXX_', '_TEMP_', '_DUP_', '_CPY_'):
		if license.startswith(prefix):
			license = license[len(prefix):]
			license = license[:10]
			break
	
	# Try to find a trailing decimal component of the license code.
	result = reNumEnd.search( license )
	if result:
		# Get the text and number component of the license code.
		num = license[result.start():result.end()]
		num_count = len(num)
		text = license[:result.start()] if num_count < 15 else ''
		text_count = len(text)
	else:
		# This license code has no numeric component.
		text = license
		text_count = len(text)
		num = '0'
		num_count = 0
		
	assert text_count <= 10, 'Maximum allowed text chars is 10'
	assert num_count <= 15, 'Maximum allowed num chars is 15'
	
	if num_count:
		return '{tag_from_license_id:02X}{text_count:X}{num_count:X}{text_hex}{num:0{byte_count}X}'.format(
			tag_from_license_id=255-tag_from_license_id,
			text_count = text_count,
			num_count = num_count,
			text_hex=''.join( '{:02X}'.format(ord(c)) for c in text ),
			num=int(num),
			byte_count=bytes_from_digits[num_count]*2,
		)
	else:
		return '{tag_from_license_id:02X}{text_count:X}0{text_hex}'.format(
			tag_from_license_id=255-tag_from_license_id,
			text_count = text_count,
			text_hex=''.join( '{:02X}'.format(ord(c)) for c in text ),
		)

def getLicenseFromTag( tag, tag_from_license_id=0 ):
	# Get the tag id from the first 2 hex characters.
	try:
		tflid = int( tag[0:2], 16 )
	except ValueError:
		return None
	
	if tflid != 255-tag_from_license_id:
		return None

	# Now get the text_count and num_count from the next text chars.
	prefix_count = 2
	try:
		text_count = int( tag[prefix_count], 16 )
		num_count = int( tag[prefix_count+1], 16 )
	except ValueError:
		return None
	
	# Check that this is an allowable text length.
	if text_count > 10:
		return None
	
	# Get the ascii characters.
	prefix_count += 2
	try:
		text = ''.join( chr(int(tag[i:i+2], 16)) for i in range(prefix_count, prefix_count+text_count*2, 2) )
	except ValueError:
		return None
	
	if len(text) != text_count:
		return None
	
	if not num_count:
		return text
	
	prefix_count += text_count*2
	
	# Get the number of bytes required to represent a decimal number of num_count characters.
	byte_count = bytes_from_digits[num_count]
	
	# Get the hex string based on the number of bytes.
	hex_text = tag[prefix_count:prefix_count+byte_count*2]
	if len(hex_text) != byte_count*2:
		return None
	
	# Convert the hex string into a number.
	try:
		num = int( hex_text, 16 )
	except ValueError:
		return None
	
	# Return the ascii and number formatted to the correct length.
	return text + '{}'.format(num).rjust( num_count, '0' )

if __name__ == '__main__':
	for license in ('CAN19650922', 'ON0123', 'BC0567', 'SK9999', '123567', 'ALLTEXT', '', '999999999999999', 'ABCDEFGHIJ', '_XXX_UMM2TLHSTBNI94ESDHQYIG81LFA'):
		tag = getTagFromLicense( license )
		license_new = getLicenseFromTag( tag )
		print ( '"{}" {} ({}) "{}"'.format(license, tag, len(tag), license_new) )
		assert license.startswith('_') or license == license_new
	
	assert getLicenseFromTag( 'FE00' ) == None
	assert getLicenseFromTag( 'FF10' ) == None
	assert getLicenseFromTag( 'FF01' ) == None
	assert getLicenseFromTag( 'FF0601E2AF' ) == '123567'
