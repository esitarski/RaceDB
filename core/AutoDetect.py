import re
import socket
import subprocess
from pyllrp.pyllrp import *

def GetDefaultHost():
	DEFAULT_HOST = socket.gethostbyname(socket.gethostname())
	if DEFAULT_HOST == '127.0.0.1':
		reSplit = re.compile('[: \t]+')
		try:
			co = subprocess.Popen(['ifconfig'], stdout = subprocess.PIPE)
			ifconfig = co.stdout.read()
			for line in ifconfig.split('\n'):
				line = line.strip()
				try:
					if line.startswith('inet addr:'):
						fields = reSplit.split( line )
						addr = fields[2]
						if addr != '127.0.0.1':
							DEFAULT_HOST = addr
							break
				except:
					pass
		except:
			pass
	return DEFAULT_HOST
	
def findImpinjHost( impinjPort, callback = None ):
	''' Search ip addresses adjacent to the computer in an attempt to find the reader. '''
	ip = [int(i) for i in GetDefaultHost().split('.')]
	j = 0
	for i in range(14):
		j = -j if j > 0 else -j + 1
		
		ipTest = list( ip )
		ipTest[-1] += j
		if not (0 <= ipTest[-1] < 256):
			continue
			
		impinjHost = '.'.join( '{}'.format(v) for v in ipTest )
		
		if callback:
			callback( '{}:{}'.format(impinjHost, impinjPort) )
		
		readerSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		readerSocket.settimeout( 4.0 )
		try:
			readerSocket.connect( (impinjHost, impinjPort) )
		except Exception as e:
			continue
		
		try:
			response = UnpackMessageFromSocket( readerSocket )
		except Exception as e:
			readerSocket.close()
			continue
			
		readerSocket.close()
		
		# Check if the connection succeeded.
		connectionAttemptEvent = response.getFirstParameterByClass(ConnectionAttemptEvent_Parameter)
		if connectionAttemptEvent and connectionAttemptEvent.Status == ConnectionAttemptStatusType.Success:
			if callback:
				callback( 'Success!' )
			return impinjHost
	
	return None

def AutoDetect( impinjPort = 5084, callback = None ):
	return findImpinjHost( impinjPort, callback )
		
if __name__ == '__main__':
	def cb( message ):
		print ( 'message: {}...',format(message) )
	ret = AutoDetect(5084, cb)
	print ( 'AutoDetect returned: {}'.format(ret) )
