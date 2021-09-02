import traceback
from .LLRPClientServer import LLRPClient

def _get_client():
	return LLRPClient()

def WriteTag( tag, antenna ):
	client = _get_client()
	try:
		return client.write( tag, antenna )
	except Exception as e:
		return False, dict(errors=['{}'.format(e), '{}'.format(traceback.format_exc())])
		
def ReadTag( antenna ):
	client = _get_client()
	try:
		return client.read( antenna )
	except Exception as e:
		return False, dict(errors=['{}'.format(e), '{}'.format(traceback.format_exc())])
	
