from models import *

from django.db.models import Q
from django.db import transaction, IntegrityError

from TagFormat import getLicenseFromTag
from models import SystemInfo

def add_participant_from_license_holder( competition, license_holder ):
	# Try to create a new participant from the license_holder and return that.
	participant = Participant( competition=competition, license_holder=license_holder, preregistered=False ).init_default_values()
	try:
		participant.save()
		participant.add_to_default_optional_events()
		return license_holder, [participant]
		
	except IntegrityError as e:
		# If this participant exists already, recover silently by going directly to the existing participant.
		participants = list(Participant.objects.filter(competition=competition, license_holder=license_holder))
		participants.sort( key = lambda p: p.category.sequence if p.category else p.bib )
		return license_holder, participants

def participant_key_filter( competition, key, auto_add_participant=True ):
	# Convert the key to upper.
	# The license_code, tag and tag2 are all stored in upper-case, so it is safe to do
	# exact matches.
	key = key.strip().upper().lstrip('0')
	
	if not key:
		return None, []
	
	# First check for an existing participant.
	participants = list( Participant.objects.filter( competition=competition ).filter(
		Q(license_holder__license_code=key) | Q(tag=key) | Q(tag2=key)) )
	
	if participants:
		participants.sort( key = lambda p: p.category.sequence if p.category else p.bib )
		return participants[0].license_holder, participants
	
	# Check for a license encoded in an rfid tag.
	tag_original = None
	if competition.using_tags and competition.use_existing_tags:
		system_info = SystemInfo.get_singleton()
		if system_info.tag_from_license:
			license_from_tag = getLicenseFromTag( key, system_info.tag_from_license_id )
			if license_from_tag is not None:
				tag_original = key
				key = license_from_tag
	
	# Second, check for a license holder matching the key.
	if competition.using_tags and competition.use_existing_tags:
		q = Q(license_code=key) | Q(existing_tag=key) | Q(existing_tag2=key)
	else:
		q = Q(license_code=key)
	
	try:
		license_holder = LicenseHolder.objects.get( q )
	except LicenseHolder.DoesNotExist as e:
		license_holder = None
	except LicenseHolder.MultipleObjectsReturned as e:
		license_holder = None
	
	if not license_holder:
		return None, []			# No license holder.
		
	if competition.using_tags and competition.use_existing_tags and tag_original and license_holder.existing_tag != tag_original:
		license_holder.existing_tag = tag_original
		license_holder.save()
	
	if not auto_add_participant:
		return license_holder, []
	
	return add_participant_from_license_holder( competition, license_holder )
