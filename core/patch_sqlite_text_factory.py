import six
import types

# Put the encodings you expect in sequence.
# Right-to-left charsets are not included in the following list.
encodings = (
	'utf-8',
	'iso-8859-1', 'iso-8859-2', 'iso-8859-3',
	'iso-8859-4', 'iso-8859-5',
	'iso-8859-7', 'iso-8859-8', 'iso-8859-9',
	'iso-8859-10', 'iso-8859-11',
	'iso-8859-13', 'iso-8859-14', 'iso-8859-15',
	'windows-1250', 'windows-1251', 'windows-1252',
	'windows-1253', 'windows-1254', 'windows-1255',
	'windows-1257', 'windows-1258',
)

def to_unicode(s):
	''' Try a number of encodings in an attempt to convert the text to unicode. '''
	if not isinstance( s, bytes ):
		return u'{}'.format(s)

	for encoding in encodings:
		try:
			return s.decode(encoding)
		except Exception as e:
			pass
	# If we don't find a valid encoding, use utf-8 and ignore any errors.
	return s.decode('utf-8', 'ignore')

try:
	from django.db.backends.sqlite3.base import DatabaseWrapper
	if not hasattr(DatabaseWrapper, 'get_new_connection_is_patched'):
		_get_new_connection = DatabaseWrapper.get_new_connection
		def get_new_connection_tolerant(self, conn_params):
			conn = _get_new_connection( self, conn_params )
			conn.text_factory = to_unicode
			return conn

		if six.PY2:
			DatabaseWrapper.get_new_connection = types.MethodType( get_new_connection_tolerant, None, DatabaseWrapper )
		else:
			DatabaseWrapper.get_new_connection = types.MethodType( get_new_connection_tolerant, DatabaseWrapper )
		DatabaseWrapper.get_new_connection_is_patched = True
		print ( 'patch_sqlite_text_factor: successfully applied multi-encoding text decoder' )
except Exception as e:
	pass	# If we get an sqlite version error, ignore and let another part of Django raise it.
