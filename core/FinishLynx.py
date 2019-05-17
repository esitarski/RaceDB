import csv
import socket
import getpass
import zipfile
import operator
import datetime
try:
	from StringIO import StringIO
	BytesIO = StringIO
except:
	from io import BytesIO, StringIO

from .models import *

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
	sep = u';' + u'-' * 78 + u'\n'
	for fname, io_stream in fnameIOs:
		header = [
			u'{}: FinishLynx database file'.format(fname),
			u'',
			u'Created by: RaceDB v{} (www.sites.google.com/site/crossmgrsoftware/)'.format(RaceDBVersion),
			u'Timestamp: {}'.format( timestamp ),
			u'Server: {}'.format( socket.gethostname() ),
			u'UserName: {}'.format( getpass.getuser() ),
			u'',
			u'See FinishLynx documentation for details (http://www.finishlynx.com/).',
		]
		io_stream.write( sep )
		for h in header:
			io_stream.write( u'{}'.format('; {}\n'.format(h)) )
		io_stream.write( sep )
			
	bibs = set()
	
	finishLynxEventNum = 0

	for event in sorted( competition.get_events(), key=operator.attrgetter('date_time') ):
		finishLynxEventNum += 1
		evtWriter.writerow( [u'{}'.format(v) for v in ([finishLynxEventNum, 1, 1, u'{}-{}'.format(event.name, competition.name)])] )
		schWriter.writerow( [u'{}'.format(v) for v in ([finishLynxEventNum, 1, 1])] )
		for p in sorted( event.get_participants(), key = lambda participant: participant.bib if participant.bib else -1 ):
			if not p.bib:
				continue
			if p.bib not in bibs:
				bibs.add( p.bib )
				pplWriter.writerow( [u'{}'.format(v) for v in 
						(p.bib, p.license_holder.last_name, p.license_holder.first_name, p.team.name if p.team else u'')
					]
				)
			evtWriter.writerow( [u'{}'.format(v) for v in ([u'', p.bib])] )
	
	zipIO = BytesIO()
	with zipfile.ZipFile(zipIO, 'w') as zip:
		for fname, io in fnameIOs:
			zip.writestr( fname, io.getvalue() )
			io.close()
	
	return zipIO.getvalue()
	
