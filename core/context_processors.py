from utils import Breadcrumbs

def standard( request ):
	bc = Breadcrumbs( request.path )
	return {
		'path':			request.path,
		'breadcrumbs':	bc.breadcrumbs,
		'cancelUrl':	bc.cancelUrl,
		'popUrl':		bc.popUrl,
		'pop2Url':		bc.pop2Url,
		'pop3Url':		bc.pop3Url,
		'title':		bc.title,
	}

def getContext( request, key ):
	return standard(request)[key]
