from django.db import models
from django.http import HttpRequest
import sys
import datetime
import platform
import traceback
import threading
import random
import time
from os.path import expanduser
from os import environ
import threading
from queue import Queue, Empty
from .utils import removeDiacritic, safe_print

global logFileName
logFileName = '{}/RaceDBLog.txt'.format(expanduser("~"))
try:
    logFileName = environ['RACEDBLOGFILE']
except Exception:
    None
sys.stderr.write( 'logFileName="{}"\n'.format(logFileName) )

# Use a singleton thread to write the log to avoid clobbering log writes.
logThread = None
messageQ = None
def messageWriter():
	time.sleep( random.random() * 10.0 )
	output = []
	while 1:
		# Collect all available log messages.
		while 1:
			try:
				message = messageQ.get( False )
			except Empty:
				break
			output.append( message )
			messageQ.task_done()
		
		# Write all log messages in one call to minimize IO.
		if output:
			try:
				with open(logFileName, 'a') as fp:
					fp.write( ''.join(output) )
				output = []
			except Exception as e:
				safe_print( e )
		
		# Sleep a random duration to minimize file write collisions between multiple RaceDB instances.
		time.sleep( 60.0 + random.random() * 60.0 * 4.0 )

PlatformName = platform.system()
def writeLog( message ):
	global logThread, messageQ
	
	if not logThread:
		messageQ = Queue()
		logThread = threading.Thread( target=messageWriter )
		logThread.daemon = True
		logThread.start()
		writeLog( '****** Log Initialized *****' )

	dt = datetime.datetime.now()
	dt = dt.replace( microsecond = 0 )
	messageQ.put( '{} ({}) {}{}'.format(
			dt.isoformat(),
			PlatformName,
			message, '\n' if not message or message[-1] != '\n' else '',
		),
	)

def logCall( f ):
	def _getstr( x ):
		if isinstance(x, HttpRequest):
			fields = [ 'server="{}:{}"'.format(x.META.get('SERVER_NAME'), x.META.get('SERVER_PORT')) ] + [
				'{}="{}"'.format( n.lower(), x.META.get(n) ) for n in [
					'REMOTE_HOST',
					'REMOTE_ADDR',
					'REMOTE_USER',
					] if x.META.get(n, '')
			] + ['username="{}"'.format(x.user.username)] + ['path="{}"'.format(x.path)]
			return u', '.join( fields )
		elif isinstance(x, models.Model):
			return u'<<{}>>'.format(x.__class__.__name__)
		return u'{}'.format(x)
	
	def new_f( *args, **kwargs ):
		parameters = [_getstr(a) for a in args] + [ u'{}={}'.format( key, _getstr(value) ) for key, value in kwargs.items() ]
		writeLog( '{}({})'.format(f.__name__, removeDiacritic(u', '.join(parameters))) )
		return f( *args, **kwargs)
	return new_f
	
def logException( e, exc_info ):
	eType, eValue, eTraceback = exc_info
	ex = traceback.format_exception( eType, eValue, eTraceback )
	writeLog( '**** Begin Exception ****' )
	for d in ex:
		for line in d.split( '\n' ):
			writeLog( line )
	writeLog( '**** End Exception ****' )
