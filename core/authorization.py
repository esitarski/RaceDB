import os
from secrets import randbelow
from base64 import urlsafe_b64encode, urlsafe_b64decode

racedb_secret_fname = os.path.join( os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'RaceDBSecret.txt' )

def get_secret_key():
	username = 'cloud'
	try:
		with open(racedb_secret_fname, 'r') as f:
			password = f.read().strip().split('\n')[0]
	except Exception:
		password = 'secret'
	return username, password

def get_secret_authorization():
	username, password = get_secret_key()
	
	a = '{}:{}'.format(username, password)
	k = randbelow(128)
	def add_k( c ):
		return chr((ord(c)+k)%127)
	
	ac = [chr(k)]
	for i in range(4):
		ac.append( chr(randbelow(128)) )
	for c in a:
		for i in range(randbelow(3)):
			ac.append( add_k(chr(randbelow(7))) )
		ac.append( add_k(c) )
	for i in range(randbelow(5)):
		ac.append( add_k(chr(randbelow(8))) )
	return 'Basic ' + urlsafe_b64encode(''.join(ac).encode()).decode()
	
def validate_secret_authorization( a ):
	try:
		a = urlsafe_b64decode(a.split()[1].encode()).decode()
		k = ord(a[0])
		def sub_k( c ):
			return chr((ord(c)+127-k)%127)
		s = ''.join(sub_k(c) for c in a[5:])
		s = ''.join( c for c in s if ord(c) > 7 )
		username, password = s.split(':', 1)
	except Exception as e:
		return False
	return (username, password) == get_secret_key()

def validate_secret_request( request ):
	return request.META.has_key('HTTP_AUTHORIZATION') and validate_secret_authorization(request.META['HTTP_AUTHORIZATION'])
		
if __name__ == '__main__':
	for i in range(50):
		a = get_secret_authorization()
		v = validate_secret_authorization( a )
		print ( '{}, {}'.format(a, v) )
