import socket
import select
import json
import time
import datetime
import threading
import argparse
import random
from Queue import Queue, Empty

import traceback

from pyllrp import *
from pyllrp.TagInventory import TagInventory
from pyllrp.TagWriter import TagWriter
from AutoDetect import AutoDetect

#-----------------------------------------------------------------------
# Find a unique port for the LLRPServer.
# Required for simultaneous instances of RaceDB.
#
def findUnusedPort( host='localhost', portStart=50111, portRange=10 ):
	ports = list(xrange(portStart, portStart+portRange))
	random.shuffle( ports )
	for port in ports:
		try:
			server = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			server.bind( (host, port) )
			server.listen( 5 )
			server.close()
			return port
		except Exception as e:
			pass
	return None

defaultPort = None

def getDefaultPort( host='localhost' ):
	global defaultPort
	if defaultPort is None:
		defaultPort = findUnusedPort( host=host )
	return defaultPort
	
#-----------------------------------------------------------------------

terminator = bytes('\r\n')
HexChars = set( '0123456789ABCDEF' )

def receiveAll( s ):
	data = ''
	while not data.endswith( terminator ):
		data += s.recv( 1024 )
	return data

def marshal( message ):
	message['timestamp'] = datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S.%f' )[:-3]
	return ''.join([json.dumps(message), terminator])

def unmarshal( messageStr ):
	if messageStr.endswith( terminator ):
		messageStr = messageStr[:-len(terminator)]
	return json.loads( messageStr )

def sendMessage( s, message ):
	s.sendall( marshal(message) )

def receiveMessage( s ):
	return unmarshal( receiveAll(s) )

def transact( s, message ):
	sendMessage( s, message )
	return receiveMessage( s )

class LLRPServer( threading.Thread ):
	def __init__( self, LLRPHostFunc, host='localhost', port=None, transmitPower=None, receiverSensitivity=None, messageQ=None ):
		self.LLRPHostFunc = LLRPHostFunc
		
		self.host = host
		self.port = getDefaultPort( host=self.host ) if port is None else port
		print 'LLRPServer: init: ', self.host, self.port
		
		self.tagWriter = None
		self.transmitPower = transmitPower
		self.receiverSensitivity = receiverSensitivity
		self.messageQ = messageQ
		self.exception_termination = False
		self.llrp_host = None
		super(LLRPServer, self).__init__( name='LLRPServer' )
		self.daemon = True

	def logMessage( self, *args ):
		if self.messageQ:
			self.messageQ.put( ' '.join(str(a).strip() for a in args) )
	
	def shutdown( self ):
		s = self.getClientSocket()
		
		try:
			sendMessage( s, dict(cmd='shutdown') )
		except Exception as e:
			self.logMessage( 'shutdown exception:', e )
		
		try:
			s.close()
		except Exception as e:
			self.logMessage( 's.close() exception:', e )
		
		if self.tagWriter:
			try:
				self.tagWriter.Disconnect()
			except Exception as e:
				self.logMessage( 'tagWriter.Disconnect() exception:', e )
			self.tagWriter = None
		
		self.logMessage( 'shutdown complete' )
	
	def connectTagWriter( self ):
		self.llrp_host = self.LLRPHostFunc()
		self.tagWriter = TagWriter( self.llrp_host, transmitPower=self.transmitPower, receiverSensitivity=self.receiverSensitivity )
		self.tagWriter.Connect()
	
	def connect( self ):
		if self.is_alive():
			self.shutdown()
			
		self.connectTagWriter()
		self.start()
		self.logMessage( 'connect success' )
	
	def getClientSocket( self ):
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		s.connect( (self.host, self.port) )
		return s
		
	def transact( self, message ):
		return transact( self.getClientSocket(), message )
	
	def handleRequest( self, request ):
		message = unmarshal( request )
		cmd = message['cmd']
		
		if   cmd == 'write':
			try:
				success, errors = self.writeTag( message['tag'], message['antenna'] )
				return marshal( dict(success=success, tag=message['tag'], antenna=message['antenna'], errors=errors) ), True
			except Exception as e:
				return marshal( dict(success=False, tag=message['tag'], antenna=message['antenna'],
								errors=[unicode(e), traceback.format_exc()]) ), True
		
		elif cmd == 'read':
			try:
				tags, errors = self.readTags( antenna=message['antenna'] )
				return marshal( dict(success=not errors, tags=tags, antenna=message['antenna'], errors=errors) ), True
			except Exception as e:
				return marshal( dict(success=False, antenna=message['antenna'], errors=[unicode(e), traceback.format_exc()]) ), True
		
		elif cmd == 'status':
			return marshal( dict(success=True) ), True
		
		elif cmd == 'shutdown':
			return marshal( dict(success=True) ), False
		
		else:
			return ( dict(success=False, errors=['Unknown request']) ), True
	
	def writeTag( self, tag, antenna, callCount = 0 ):
		errors = []
		
		tag = str(tag).lstrip('0').upper()
		if not tag:
			errors.append( 'Tag Write Failure: Tag is empty.  Nothing written.' )
			return False, errors
			
		if not all( c in HexChars for c in tag ):
			errors.append( 'Tag Write Failure: Tag has non-hex characters.' )
			return False, errors
			
		try:
			antenna = int(antenna)
		except:
			errors.append( 'Tag Write Failure: Invalid antenna.  Must be 1, 2, 3 or 4.' )
			return False, errors
		
		if not (1 <= antenna <= 4):
			errors.append( 'Tag Write Failure: Antenna not in range.  Must be 1, 2, 3 or 4.' )
			return False, errors
			
		try:
			self.tagWriter.WriteTag( '', tag, antenna )
		except Exception as e:
			eOriginal = e
			self.logMessage( 'tagWriter.WriteTag("","{}",{}) fails: {}'.format(tag, antenna, eOriginal) )
			if callCount == 0:
				self.logMessage( 'Attempting reader reconnect.' )
				try:
					self.connectTagWriter()
					return self.writeTag( tag, antenna, callCount+1 )
				
				except Exception as e:
					errors.append( 'Tag Write Failure: {}.'.format(eOriginal) )
					errors.append( 'Reader reconnect failure: {}.'.format(e) )
					errors.append( traceback.format_exc() )
					return False, errors
				
			errors.append( 'Tag Write Failure: {}.'.format(e) )
			errors.append( traceback.format_exc() )
			return False, errors
			
		time.sleep( 50.0/1000.0 )	# Give the reader some time to work.
		
		tagInventory = None
		try:
			tagInventory, otherMessages = self.tagWriter.GetTagInventory( antenna )
			tagInventory = [(t or '0') for t in sorted(tagInventory, key = lambda x: int(x or '0',16))]
			
			if len(tagInventory) == 0:
				errors.append( 'Tag Verify Failure: Failed to read new tag value after write.' )
			elif len(tagInventory) == 1:
				if tagInventory[0] != tag:
					errors.append( 'Tag Verify Failure: Tag value read {} fails to match tag value written {}.'.format(
						tagInventory[0],
						tag,
					))
			else:
				if tag in tagInventory:
					errors.append( 'Tag Verify Warning: New tag value read {} but additional tags also read during validation ({}).'.format(
						tag,
						', '.join(t for t in tagInventory if t != tag),
					))
				else:
					errors.append( 'Tag Verify Failure: Failed to read new tag value {} but additional tags read during validation ({}).'.format(
						tag,
						', '.join(tagInventory),
					))
		except Exception as e:
			errors.append( 'Tag Verify Failure: {}.'.format(e) )
			
		return not errors, errors
	
	def readTags( self, antenna, callCount=0 ):
		errors = []
		tagInventory = []
		try:
			tagInventory, otherMessages = self.tagWriter.GetTagInventory( antenna )
			if not tagInventory:
				errors.append( 'No tags read.' )
		except Exception as e:
			eOriginal = e
			self.logMessage( 'tagWriter.GetTagInventory({}) fails: {}'.format(antenna, eOriginal) )
			if callCount == 0:
				self.logMessage( 'Attempting reader reconnect.' )
				try:
					self.connectTagWriter()
					return self.readTags( antenna, callCount+1 )
				except Exception as e:
					errors.append( 'Read Tag Failure: {}'.format(eOriginal) )
					errors.append( 'Reader reconnect failure: {}.'.format(e) )
					errors.append( traceback.format_exc() )
					return [], errors
			
			errors.append( 'Read Tag Failure: {}'.format(e) )
			errors.append( traceback.format_exc() )
			
		return [tag.lstrip('0') for tag in tagInventory], errors
	
	def run( self ):
		size = 1024
		self.exception_termination = False
		
		server = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		
		server.bind( (self.host, self.port) )
		server.listen( 5 )
		
		input = [server]
		output = []
		
		inputdata = {}
		outputdata = {}

		running = True
		while running: 
			inputready, outputready, exceptready = select.select( input, output, [] ) 
			
			for s in inputready: 
				if s is server: 
					client, address = server.accept() 
					input.append( client )
					inputdata[client] = bytes()
					continue
				
				data = s.recv( size )
				if data:
					inputdata[s] += data
					if inputdata[s].endswith( terminator ):
					
						self.logMessage( 'Request:', inputdata[s] )
						try:
							outputdata[s], running = self.handleRequest( inputdata[s] )
						except Exception as e:
							self.logMessage( 'Exception:', e )
							self.exception_termination = True
							break
						self.logMessage( 'Reply:', outputdata[s] )
						
						del inputdata[s]
						input.remove( s )
						
						if outputdata[s]:
							output.append( s )
						else:
							del outputdata[s]
							s.close()
				else: 
					del inputdata[s]
					input.remove( s )
					s.close() 
			
			for s in outputready:
				count = s.send( outputdata[s] )
				if count == len(outputdata[s]):
					output.remove( s )
					del outputdata[s]
					s.close()
				else:
					outputdata[s] = outputdata[s][count:]
		
		server.close()

class LLRPClient( object ):
	def __init__( self, host='localhost', port=None ):
		self.host = host
		self.port = getDefaultPort( host=self.host ) if port is None else port
	
	def sendCmd( self, **kwargs ):
		try:
			s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			s.connect( (self.host, self.port) )
			response = transact( s, kwargs )
			s.close()
			return response.get('success', False), response
		except Exception as e:
			return False, dict(errors=[u'{}'.format(e)])
	
	def write( self, tag, antenna ):
		return self.sendCmd( cmd='write', tag=tag, antenna=antenna )
		
	def read( self, antenna ):
		return self.sendCmd( cmd='read', antenna=antenna )
	
	def status( self ):
		return self.sendCmd( cmd='status' )
	
def writeLog( message ):
	print u'[LLRPServer {}]  {}'.format( datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message )

def doAutoDetect():
	LLRPHost = AutoDetect( callback=lambda m: writeLog('AutoDetect Checking: ' + m) )
	if LLRPHost:
		writeLog( 'AutoDetect: LLRP Reader found on ({}:{})'.format(LLRPHost, 5084) )
	return LLRPHost
	
def runServer( host='localhost', llrp_host=None, transmitPower=None, receiverSensitivity=None ):
	messageQ = Queue()
	
	transmitPower = transmitPower if transmitPower else None
	receiverSensitivity = receiverSensitivity if receiverSensitivity else None
	
	server = None
	retryDelaySeconds = 3
	
	# Define function to get llrp_host name.
	if llrp_host and llrp_host.lower() != 'autodetect':
		LLRPHostFunc = lambda : llrp_host
	else:
		LLRPHostFunc = doAutoDetect
	
	# Outer loop - connect/reconnect to the reader.
	while True:
		if server is not None:
			writeLog( 'Attempting reconnect in {} seconds...'.format(retryDelaySeconds) )
			time.sleep( retryDelaySeconds )
		
		server = LLRPServer( LLRPHostFunc=LLRPHostFunc, messageQ=messageQ, transmitPower=transmitPower, receiverSensitivity=receiverSensitivity )
		writeLog( 'runServer: LLRP Server on ({}:{})'.format(server.host, server.port) )
	
		try:
			server.connect()
			writeLog( 'runServer: Successfully connected to ({}:5084)!'.format(server.llrp_host) )
		except Exception as e:
			writeLog( 'runServer: {}'.format(e) )
			writeLog( 'runServer: Connection to ({}:5084) fails.'.format(server.llrp_host) )
			continue
		
		# Inner loop - process messages from the reader.
		while True:
			writeLog( 'runServer: Server: ' + messageQ.get() )
			messageQ.task_done()
			if server.exception_termination:
				writeLog( 'runServer: Exceptional RFID Reader Termination.' )
				break
