from waitress import serve

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core import management
#from whitenoise.django import DjangoWhiteNoise

from dj_static import Cling

import threading
import time
import socket
import webbrowser

import RaceDB.wsgi
import RaceDB.urls
from core.LLRPClientServer import runServer
from core.models import SystemInfo, models_fix_data

def launch_server( **options ):

	# Migrate the database automatically.
	print 'Performing database migration (if necessary)...'
	#management.call_command('migrate', '--noinput', verbosity=0)
	
	models_fix_data()

	# Start the rfid server.
	if any([options['rfid_reader'], options['rfid_reader_host'], options['rfid_transmit_power'] > 0, options['rfid_receiver_sensitivity'] > 0]):
		kwargs = {
			'llrp_host': options['rfid_reader_host'],
		}
		if options['rfid_transmit_power'] > 0:
			kwargs['transmitPower'] = options['rfid_transmit_power']
		if options['rfid_receiver_sensitivity'] > 0:
			kwargs['receiverSensitivity'] = options['rfid_receiver_sensitivity']
		print 'Launching RFID server thread...'
		for k, v in kwargs.iteritems():
			print '    {}={}'.format( k, v if isinstance(v, (int,long,float)) else '"{}"'.format(v) )
		thread = threading.Thread( target=runServer, kwargs=kwargs )
		thread.name = 'LLRPServer'
		thread.daemon = True
		thread.start()
		time.sleep( 0.5 )
	
	if not options['no_browser']:
		# Schedule a web browser to launch a few seconds after starting the server.
		url = 'http://{}:{}/RaceDB/'.format(socket.gethostbyname(socket.gethostname()), options['port'])
		threading.Timer( 3.0,
			webbrowser.open,
			kwargs = dict(
				url = url,
				autoraise = True
			)
		).start()
		print 'A browser will be launched in a few moments at: {}'.format(url)
		
	print 'To stop the server, click in this window and press Ctrl-c.'

	# Add DjangoWhiteNoise to serve up static files efficiently in waitress.
	#serve( DjangoWhiteNoise(RaceDB.wsgi.application), host=options['host'], port=options['port'], threads=10 )
	serve( Cling(RaceDB.wsgi.application), host=options['host'], port=options['port'], threads=10 )

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
			help='Database file to access')
					
	def handle(self, *args, **options):
		launch_server( **options )

