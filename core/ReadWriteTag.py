
from models import SystemInfo
from LLRPClientServer import LLRPClient
import traceback

def _get_client():
	system_info = SystemInfo.get_singleton()
	return LLRPClient( system_info.rfid_server_host, system_info.rfid_server_port )

def WriteTag( tag, antenna ):
	client = _get_client()
	try:
		return client.write( tag, antenna )
	except Exception as e:
		return False, dict(errors=[u'{}'.format(e), u'{}'.format(traceback.format_exc())])
		
def ReadTag( antenna ):
	client = _get_client()
	try:
		return client.read( antenna )
	except Exception as e:
		return False, dict(errors=[u'{}'.format(e), u'{}'.format(traceback.format_exc())])
	
