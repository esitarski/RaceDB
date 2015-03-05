import types
from django.db.backends.sqlite3.base import DatabaseWrapper

def to_unicode( s ):
    ''' Try a number of encodings in an attempt to convert the text to unicode. '''
    if isinstance( s, unicode ):
        return s
    if not isinstance( s, str ):
        return unicode(s)
    
    # Put the encodings you expect here in sequence.
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
    for encoding in encodings:
        try:
            return unicode( s, encoding )
        except UnicodeDecodeError as e:
            pass
    return unicode( s, 'utf-8', 'ignore' )

if not hasattr(DatabaseWrapper, 'get_new_connection_is_patched'):
    _get_new_connection = DatabaseWrapper.get_new_connection
    def get_new_connection_tolerant(self, conn_params):
        conn = _get_new_connection( self, conn_params )
        conn.text_factory = to_unicode
        return conn

    DatabaseWrapper.get_new_connection = types.MethodType( get_new_connection_tolerant, None, DatabaseWrapper )
    DatabaseWrapper.get_new_connection_is_patched = True
