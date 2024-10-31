from sys import stderr
from functools import wraps, partial
import traceback

def IgnoreException( func ):
	''' Wrap a function to ignore any exception raised. '''
	@wraps( func )
	def wrapper( *args, **kwargs ):
		try:
			return func( *args, **kwargs )
		except Exception as e:
			traceback.print_exc( file=stderr )
			p = partial( print, file=stderr )
			p( '**** Ignore Exception:' )
			p( f'    function:  {func.__name__}' )
			p( f'    exception: {e}' )
	return wrapper

def IgnoreExceptionSubclass( cls ):
	''' Create a subclass where all user member functions are wrapped in IgnoreException. '''
	class c( cls ):
		pass
	
	for name in dir(c):
		if callable(getattr(c, name)) and not name.startswith('__'):
			setattr( c, name, IgnoreException(getattr(c, name)) )
	return c		

if __name__ == '__main__':
	def f( a, b, c='default_arg'):
		raise ValueError( 'Failure' )
		
	IgnoreException(f)( 10, 20, c='test' )
	
	print( '***************************', file=stderr )

	class A:
		def __init__( self ):
			self.v = 3
			
		def inc( self ):
			self.v += 1
			
		def dec( self ):
			self.v -= 1
			if self.v < 0:
				raise ValueError( 'below zero' )
			
	B = IgnoreExceptionSubclass( A )
	b = B()
	for i in range(5):
		b.dec()
