import csv
import getpass
import zipfile
import datetime
import socket
import StringIO

from models import *

def toUtf8( row ):
	return [unicode(v).encode('utf-8') for v in row]

def getWriterIO():
	io = StringIO.StringIO()
	writer = csv.writer( io )
	return writer, io
	
def FinishLynxExport( competition ):
	
	pplWriter, pplIO = getWriterIO()
	evtWriter, evtIO = getWriterIO()
	schWriter, schIO = getWriterIO()
	
	fnameIOs = (('lynx.ppl', pplIO), ('lynx.evt', evtIO), ('lynx.sch', schIO))
	
	timestamp = datetime.datetime.now().strftime('%Y/%d/%m %H:%M:%S.%f')
	sep = ';' + '-' * 78 + '\n'
	for fname, io in fnameIOs:
		header = [
			'{}: FinishLynx database file'.format(fname),
			'',
			'Created by: RaceDB v{} (www.sites.google.com/site/crossmgrsoftware/)'.format(RaceDBVersion),
			'Timestamp: {}'.format( timestamp ),
			'Server: {}'.format( socket.gethostname() ),
			'UserName: {}'.format( getpass.getuser() ),
			'',
			'See FinishLynx documentation for details (http://www.finishlynx.com/).',
		]
		io.write( sep )
		for h in header:
			io.write( unicode('; {}\n'.format(h)).encode('utf-8') )
		io.write( sep )
			
	bibs = set()
	
	finishLynxEventNum = 0

	for event in sorted( competition.get_events(), key = lambda e: e.date_time ):
		finishLynxEventNum += 1
		evtWriter.writerow( toUtf8([finishLynxEventNum, 1, 1, u'{}-{}'.format(event.name, competition.name)]) )
		schWriter.writerow( toUtf8([finishLynxEventNum, 1, 1]) )
		for p in sorted( event.get_participants(), key = lambda participant: participant.bib if participant.bib else -1 ):
			if not p.bib:
				continue
			if p.bib not in bibs:
				bibs.add( p.bib )
				pplWriter.writerow( toUtf8(
					[p.bib, p.license_holder.last_name, p.license_holder.first_name, p.team.name if p.team else u'']
				) )
			evtWriter.writerow( toUtf8([u'', p.bib]) )
	
	zipIO = StringIO.StringIO()
	with zipfile.ZipFile(zipIO, 'w') as zip:
		for fname, io in fnameIOs:
			zip.writestr( fname, io.getvalue() )
			io.close()
	
	return zipIO.getvalue()
	
