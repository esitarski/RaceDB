from models import *

from django.db.models import Q
from django.db import transaction, IntegrityError

from TagFormat import getLicenseFromTag
from models import SystemInfo

import re

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
	key = key.strip()
	
	system_info = SystemInfo.get_singleton()
	
	# Check if the code has an embedded license code.
	license_code = None
	if system_info.license_code_regex:
		for license_code_regex in system_info.license_code_regex.split('||'):
			license_code_regex = license_code_regex.strip()
			try:
				license_code = re.match(license_code_regex, key).group('license_code').lstrip('0')
				break
			except Exception as e:
				pass
			
	# Convert the key to upper.
	# The license_code, tag and tag2 are all stored in upper-case, so it is safe to do exact matches.
	key = key.upper().lstrip('0')
	
	if not key:
		return None, []
		
	if competition.using_tags:
		if competition.use_existing_tags:
			tag_query = Q(license_holder__existing_tag=key) | Q(license_holder__existing_tag2=key)
		else:
			tag_query = Q(tag=key) | Q(tag2=key)
	else:
		tag_query = Q(tag=u'---')   # This will always fail as tags must be letters/numbers.
	
	# Check for an existing participant.
	if license_code:
		participants = list( Participant.objects.filter( competition=competition, role=Participant.Competitor, license_holder__license_code=license_code ) )
	else:
		participants = list( Participant.objects.filter( competition=competition, role=Participant.Competitor ).filter(
			Q(license_holder__license_code=key) | tag_query) )
	
	if participants:
		participants.sort( key = lambda p: (p.category.sequence if p.category else 999999, p.bib or 999999) )
		return participants[0].license_holder, participants
	
	# Check for a license encoded in an rfid tag.
	tag_original = None
	if competition.using_tags and competition.use_existing_tags:
		if system_info.tag_creation == 2:
			license_from_tag = getLicenseFromTag( key, system_info.tag_from_license_id )
			if license_from_tag is not None:
				tag_original = key
				key = license_from_tag
	
	# Second, check for a license holder matching the key.
	if license_code:
		q = Q(license_code=license_code)
	elif competition.using_tags and competition.use_existing_tags:
		q = Q(license_code=key) | tag_query
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

def participant_bib_filter( competition, bib ):
	# Check for an existing participant.
	participants = list( competition.participant_set.filter(bib=bib, role=Participant.Competitor).select_related('license_holder') )
	existing_license_holders = set( p.license_holder.pk for p in participants )

	# Check if we can find this bib in the number set excluding existing participants.
	if competition.number_set:
		license_holders = list( LicenseHolder.objects.filter( pk__in=
				competition.number_set.numbersetentry_set.filter(
					bib=bib, date_lost__isnull=True ).exclude(
					license_holder__pk__in=existing_license_holders).values_list('license_holder__pk', flat=True
				)
			)
		)
	else:
		license_holders = []
	
	return license_holders, participants
