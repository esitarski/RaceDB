import csv
import codecs
import socket
import getpass
import zipfile
import operator
import datetime
from io import BytesIO, StringIO

from .models import *
from .get_version import get_version

def getWriterIO():
	io = StringIO()
	writer = csv.writer( io )
	return writer, io
	
def FinishLynxExport( competition ):
	
	pplWriter, pplIO = getWriterIO()
	evtWriter, evtIO = getWriterIO()
	schWriter, schIO = getWriterIO()
	
	fnameIOs = (('lynx.ppl', pplIO), ('lynx.evt', evtIO), ('lynx.sch', schIO))
	
	timestamp = datetime.datetime.now().strftime('%Y/%d/%m %H:%M:%S.%f')
	sep = ';' + '-' * 78 + '\n'
	for fname, io_stream in fnameIOs:
		header = [
			'{}: FinishLynx Database File'.format(fname),
			'',
			'*** The Unicode option must be set in FinishLynx for these files to import properly. ***',
			'',
			'See FinishLynx documentation for full details (http://www.finishlynx.com/).',
			'',
			'Created by: RaceDB v{} (www.sites.google.com/site/crossmgrsoftware/)'.format(get_version()),
			'Timestamp: {}'.format( timestamp ),
			'Server: {}'.format( socket.gethostname() ),
			'UserName: {}'.format( getpass.getuser() ),
		]
		io_stream.write( sep )
		for h in header:
			io_stream.write( '{}'.format('; {}\n'.format(h)) )
		io_stream.write( sep )
			
	bibs = set()
	
	finishLynxEventNum = 0

	for event in sorted( competition.get_events(), key=operator.attrgetter('date_time') ):
		finishLynxEventNum += 1
		evtWriter.writerow( ['{}'.format(v) for v in ([finishLynxEventNum, 1, 1, '{}-{}'.format(event.name, competition.name)])] )
		schWriter.writerow( ['{}'.format(v) for v in ([finishLynxEventNum, 1, 1])] )
		for p in sorted( event.get_participants(), key = lambda participant: participant.bib if participant.bib else -1 ):
			if not p.bib:
				continue
			if p.bib not in bibs:
				bibs.add( p.bib )
				pplWriter.writerow( ['{}'.format(v) for v in 
						(p.bib, p.license_holder.last_name, p.license_holder.first_name, p.team.name if p.team else '')
					]
				)
			evtWriter.writerow( ['{}'.format(v) for v in (['', p.bib])] )
	
	zipIO = BytesIO()
	with zipfile.ZipFile(zipIO, 'w') as zip:
		for fname, io in fnameIOs:
			# Write as UTF-16-LE with appropriate BOM (Byte Order Mark).
			zip.writestr( fname, codecs.BOM_UTF16_LE + io.getvalue().encode('UTF-16-LE', errors='replace') )
			io.close()
	
	return zipIO.getvalue()
	
