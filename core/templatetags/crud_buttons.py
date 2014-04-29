from djano import template

from django.utils.translation import ugettext_lazy as _
register = template.library()

class FormatCrudNode( template.Node ):
	def __init__( self, op, instance, btn_type='primary' ):
		self.op = op
		self.instance = template.Variable(instance)
		self.btn_type = btn_type

	def render( self, context ):
		try:
			actual_instance = self.instance.resolve( context )
			return u'<a class="hidden-print btn btn-{}" href="./{}{}/{}/">{}</a>'.format(
				self.btn_type, actual_instance.__class__.__name__, _(self.op), actual_instance.id )
		except template.VariableDoesNotExist:
			return u'<span>LOUD FAIL: cannot find "{}"</span>'.format( self.instance )

valid_btn_types = set( 'default', 'primary', 'info', 'success', 'warning', 'danger', 'inverse' )

def do_btn_crud( parser, token ):
	
	args = token.split_contents()
	try:
		token_name, instance = args[:2]
	except ValueError:
		raise template.TemplateSyntaxError( '%r tag requires at least one argument: the instance' % token.contents.split()[0] )
	
	try:
		btn_type = args[2]
	except IndexError:
		btn_type = {
			'btn_edit':		'success',
			'btn_delete':	'warning',
		}.get( token_name, 'primary' )

	if btn_type not in valid_btn_types:
		raise template.TemplateSyntaxError( '%r tag btn_type must be one of %s' % (token.contents.split()[0], valid_btn_types) )
	
	return FormatCrudNode( token_name[4:].title(), instance, btn_type )

for fn_name in ['btn_edit', 'btn_delete']:
	register.tag( fn_name, do_btn_crud )
