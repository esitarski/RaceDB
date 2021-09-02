import waitress
from configparser import ConfigParser, NoOptionError

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core import management

from dj_static import Cling

import threading
import time
import socket
import webbrowser

import RaceDB.wsgi
import RaceDB.urls
from core.LLRPClientServer import runServer
from core.models import SystemInfo, models_fix_data
from core.utils import safe_print
from core.create_users import create_users
from core.print_bib import reset_font_cache
from core.views_common import set_hub_mode
from core.init_data import init_data_if_necessary

def check_connection( host, port ):
	safe_print( 'Checking web server connection {}:{}'.format(host,port) )
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		s.bind((host, port))
		success = True
	except socket.error as e:
		safe_print( e )
		success = False

	s.close()
	
	if success:
		safe_print( 'Web Server connection check succeeded.' )
	
	return success

class KWArgs( object ):
	def __init__( self ):
		self.kwargs = {}

	def add_argument( self, name, **info ):
		self.kwargs[info['dest']] = info
	
	def __contains__( self, dest ):
		return dest in self.kwargs
	
	def validate( self, dest, value ):
		if dest not in self.kwargs:
			return value, 'Unknown argument'
		info = self.kwargs[dest]
		
		if info.get('action', None) in ('store_true', 'store_false'):
			if isinstance(value, (int, float, long)):
				return value != 0, None
			elif isinstance(value, (str, unicode)):
				value = value.strip()
				if value[:1] in '1TtYy':
					return True, None
				elif value[:1] in '0FfNn':
					return False, None
				else:
					return value, 'value must be true/false'
			
		try:
			value = info['type'](value)
		except Exception as e:
			return value, e
			
		return value, None
		
def launch_server( command, **options ):

	# Migrate the database.
	cmd_args = {'no_input':True, 'verbosity':3}
	if options['database']:
		cmd_args['database'] = options['database']
	management.call_command( 'migrate', **cmd_args )
	
	create_users()
	models_fix_data()
	try:
		reset_font_cache()
	except Exception:
		pass
	
	# Initialize the database with pre-seeded data if it was not done.
	init_data_if_necessary()
	
	# Read the config file and adjust any options.
	config_parser = ConfigParser()
	try:
		with open(options['config'], 'r') as fp:
			config_parser.readfp( fp, options['config'] )
		safe_print( 'Read config file "{}".'.format(options['config']) )
	except Exception as e:
		if options['config'] != 'RaceDB.cfg':
			safe_print( 'Could not parse config file "{}" - {}'.format(options['config'], e) )
		config_parser = None
		
	if config_parser:
		kwargs = KWArgs()
		command.add_arguments( kwargs )
		for arg, value in list(options.items()):
			try:
				config_value = config_parser.get('launch', arg)
			except NoOptionError:
				continue
			
			config_value, error = kwargs.validate( arg, config_value )
			if error:
				safe_print( 'Error: {}={}: {}'.format(arg, config_value, error) )
				continue
			
			options[arg] = config_value
			safe_print( '    {}={}'.format( arg, config_value ) )

	if options['hub']:
		set_hub_mode( True )
		safe_print( 'Hub mode.' )
		
	# Start the rfid server.
	if not options['hub'] and any([options['rfid_reader'], options['rfid_reader_host'], options['rfid_transmit_power'] > 0, options['rfid_receiver_sensitivity'] > 0]):
		kwargs = {
			'llrp_host': options['rfid_reader_host'],
		}
		if options['rfid_transmit_power'] > 0:
			kwargs['transmitPower'] = options['rfid_transmit_power']
		if options['rfid_receiver_sensitivity'] > 0:
			kwargs['receiverSensitivity'] = options['rfid_receiver_sensitivity']
		safe_print( 'Launching RFID server thread...' )
		for k, v in kwargs.items():
			safe_print( '    {}={}'.format( k, v if isinstance(v, (int,float)) else '"{}"'.format(v) ) )
		thread = threading.Thread( target=runServer, kwargs=kwargs )
		thread.name = 'LLRPServer'
		thread.daemon = True
		thread.start()
		time.sleep( 0.5 )
	
	connection_good = check_connection( options['host'], options['port'] )

	if not options['no_browser']:
		if not connection_good:
			safe_print( 'Attempting to launch broswer connecting to an existing RaceDB server...' )
		
		# Schedule a web browser to launch a few seconds after starting the server.
		url = 'http://{}:{}/RaceDB/'.format(socket.gethostbyname(socket.gethostname()), options['port'])
		threading.Timer( 3.0 if connection_good else 0.01,
			webbrowser.open,
			kwargs = dict(
				url = url,
				autoraise = True
			)
		).start()
		safe_print( 'A browser will be launched in a few moments at: {}'.format(url) )
	
	if connection_good:
		safe_print( 'To stop the server, click in this window and press Ctrl-c.' )
		
		# Add Cling to serve up static files efficiently.
		waitress.serve( Cling(RaceDB.wsgi.application), host=options['host'], port=options['port'], threads=8, clear_untrusted_proxy_headers=False )
	else:
		time.sleep( 0.5 )
		

class Command(BaseCommand):
	
	help = 'Launch the application server'
	
	def add_arguments(self, parser):
		parser.add_argument('--host',
			dest='host',
			type=str,
			default='0.0.0.0',
			help='Host for application web server')
		parser.add_argument('--port',
			dest='port',
			type=int,
			default=8000,
			help='Port for application web server')
		parser.add_argument('--rfid_reader',
			dest='rfid_reader',
			action='store_true',
			default=False,
			help='Launch rfid reader server')
		parser.add_argument('--rfid_reader_host',
			dest='rfid_reader_host',
			type=str,
			default='',
			help='Host for RFID reader')
		parser.add_argument('--rfid_transmit_power',
			dest='rfid_transmit_power',
			type=int,
			default=0,
			help='Transmit power for rfid reader (0=max).  Consult your reader for details.')
		parser.add_argument('--rfid_receiver_sensitivity',
			dest='rfid_receiver_sensitivity',
			type=int,
			default=0,
			help='Receiver sensitivity for rfid reader (0=max).  Consult your reader for details.')
		parser.add_argument('--no_browser',
			dest='no_browser',
			action='store_true',
			default=False,
			help='Do not launch a browser')
		parser.add_argument('--database',
			dest='database',
			type=str,
			default='',
			help='Database file to use')
		parser.add_argument('--hub',
			dest='hub',
			action='store_true',
			default=False,
			help='Launch in Hub mode.')
		parser.add_argument('--config',
			dest='config',
			type=str,
			default='RaceDB.cfg',
			help='Configuration file (.cfg)')
					
	def handle(self, *args, **options):
		launch_server( self, **options )

