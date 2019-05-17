from .views_common import *

def show_emails( request, participants=[], license_holders=[], emails=[], okUrl='' ):
	emails = set( email for email in emails if email )
	emails |= set( lh.email for lh in license_holders if lh.email )
	emails |= set( p.license_holder.email for p in participants if p.license_holder.email )
	emails = sorted( emails )
	emails_length = len(emails)
	return render( request, 'emails.html', locals() )	
