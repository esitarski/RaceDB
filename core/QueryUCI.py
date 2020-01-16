import re
import json
import urllib.parse
import urllib.request
import unicodedata
import datetime

def filter_encode( s ):
	''' Remove all accents and encode as ascii. '''
	return unicodedata.normalize('NFKD', u'{}'.format(s)).encode('ASCII', 'ignore').decode()

url = 'http://ucibws.uci.ch/api/contacts/riders'

db_fields = ('first_name', 'last_name', 'uci_id')
db_uci = {f:f.replace('_','') for f in db_fields}
uci_db = {v:k for k,v in db_uci.items()}
uci_db['UCIID'] = 'uci_id'
uci_db['ridercategory'] = 'category'
uci_db['nationality'] = 'nation_code'

# Convert from UCI encoding.
uci_to_utf8 = { '\\X{:02x}'.format(i).encode():chr(i).encode() for i in range(256) }
def fix_uci_encoding( s ):
	return re.sub( rb'\\X([0-9a-f][0-9a-f])', lambda match: uci_to_utf8[match.group(0)], s )

def query_rider( category=None, team_code=None, uci_id=None, first_name=None, last_name=None, gender=None, nation_code=None, continent=None ):
	'''
		Call the UCI swagger interface.  Input/Output is in RaceDB field names.
	'''
	filter_criteria = {}
	def add_criteria( k, v ):
		filter_criteria[k] = v
	
	if category:
		if category not in ('ME', 'WE', 'MU', 'WU', 'MJ', 'WJ', 'MC', 'WC'):
			raise ValueError( 'unrecognized category.  Must be ME, WE, MU, WU, MJ, WJ, MC, WC' )
		add_criteria( 'category', category )
	if team_code:
		if len(team_code) != 3: 
			raise ValueError( 'team_code must be 3 chars' )
		add_criteria( 'teamcode', team_code )
	if uci_id is not None:
		uci_id = '{}'.format(uci_id).replace(' ','')
		if len(uci_id) != 11:
			raise ValueError( 'uci_id must be 11 characters long' )
		if not uci_id.isdigit():
			raise ValueError( 'uci_id must be all digits' )
		if int(uci_id[:-2]) % 97 != int(uci_id[-2:]):
			raise ValueError( 'uci id check digit error' )
		add_criteria( 'uciid', uci_id )
	if first_name:
		add_criteria( 'firstname', filter_encode(first_name) )
	if last_name:
		add_criteria( 'lastname', filter_encode(last_name) )
	if gender is not None:
		if isinstance(gender, int):
			gender = 'MF'[gender]
		elif gender not in 'MF':
			raise ValueError( 'gender must be M or F' )
		add_criteria( 'gender', gender )
	if nation_code:
		if len(nation_code) != 3: 
			raise ValueError( 'nation_code must be 3 chars' )
		add_criteria( 'nationality', nation_code )
	if continent:
		if continent not in ('ASI', 'AME', 'EUR', 'AFR', 'OCE'):
			raise ValueError( 'unrecognized continent.  Must be ASI, AME, EUR, AFR, OCE' )
		add_criteria( 'continent', continent )
	if not filter_criteria:
		raise ValueError( 'missing filter criteria' )
		
	data = urllib.parse.urlencode( filter_criteria, quote_via=urllib.parse.quote )
	url_full = url + '?' + data
	with urllib.request.urlopen(url_full) as response:
	   ret = response.read()			
	
	try:
		values = json.loads( ret.decode() )							# Try standard utf-8.
	except:
		values = json.loads( fix_uci_encoding(ret).decode() )		# Try non-standard encoding.
	
	if values:
		values = [{uci_db.get(k.lower(),k.lower()):v for k, v in r.items()} for r in values]
		for r in values:
			r['date_of_birth'] = None
			if 'birthdate' in r:
				try:
					r['date_of_birth'] = datetime.date( *[int(dv) for dv in r['birthdate'].split('T')[0].split('-')] )
				except:
					pass
				del r['birthdate']
			r['gender'] = None
			if 'gender' in r:
				try:
					r['gender'] = 1 if r['gender'].startswith('F') else 0
				except:
					pass
			if 'uci_id' in r:
				r['uci_id'] = '{}'.format(r['uci_id'])
	return values
		
if __name__ == '__main__':
	print( query_rider(first_name="Etienne", last_name="HOSSACK", nation_code="CAN" ) )
	print( query_rider(first_name='martin', last_name='vondrak') )	# Check unicode encoding.
	print( query_rider(first_name='Edvald Boasson') )	# Check space encoding.
	print( query_rider(uci_id='10061435134') )			# Check None for birthdate.
	#print( query_rider(first_name='edward', last_name='sitarski', gender='M') )
	#print( query_rider(first_name='anne', last_name='cobban', gender='F') )
		
