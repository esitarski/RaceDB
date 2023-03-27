from .views_common import *
from .participant import ParticipantTagUSBReaderForm
from django.utils.translation import gettext_lazy as _

@access_validation()
def CompetitionFoundTag( request, competitionId, rfid_tag=None, action=-1 ):
	competition = get_object_or_404( Competition, pk=competitionId )

	matching_license_holders = []
	
	path_noargs = '{}{}/'.format( getContext(request,'cancelUrl'), 'CompetitionFoundTag' )
	
	if request.method == 'POST':
		form = ParticipantTagUSBReaderForm( request.POST )
		if form.is_valid():
			rfid_tag = form.cleaned_data['rfid_tag'].upper().lstrip('0')
			if competition.use_existing_tags:
				matching_license_holders = list( LicenseHolder.objects.filter( Q(existing_tag=rfid_tag) | Q(existing_tag2=rfid_tag) ) )
			else:
				matching_license_holders = list( LicenseHolder.objects.filter( id__in=get_ids(competition.participant_set.filter( Q(tag=rfid_tag) | Q(tag2=rfid_tag) ), 'license_holder') ) )
		return render( request, 'competition_found_tag.html', locals() )
	
	if not rfid_tag:
		form = ParticipantTagUSBReaderForm( initial={'rfid_tag':''} )			
		return render( request, 'competition_found_tag.html', locals() )
	
	action = int(action)
	
	if action == 1:
		# Ask for confirmation to revoke the tag.
		page_title = _("Revoke this tag so it can be reused.")
		cancel_target = getContext(request,'cancelUrl')
		target = '{}{}/{}/{}/'.format( path_noargs, competition.id, rfid_tag, 2 )
		return render( request, 'are_you_sure.html', locals() )
	elif action == 2:
		# Revoke tag and reuse.
		if competition.use_existing_tags:
			LicenseHolder.objects.filter( existing_tag= rfid_tag ).update( existing_tag= None )
			LicenseHolder.objects.filter( existing_tag2=rfid_tag ).update( existing_tag2=None )
		else:
			competition.participant_set.filter( tag= rfid_tag ).update( tag= None )
			competition.participant_set.filter( tag2=rfid_tag ).update( tag2=None )
		return HttpResponseRedirect(getContext(request,'pop3Url'))
	
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
