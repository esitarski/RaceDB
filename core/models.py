from django.db import models
from django.db import transaction, IntegrityError
from django.db.models import Max
from django.db.models import Q

from django.contrib.contenttypes.models import ContentType

from django.utils.timezone import get_default_timezone
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from django.utils.safestring import mark_safe
from django.utils.translation import string_concat
from django.contrib.staticfiles.templatetags.staticfiles import static

from django.db.models.signals import pre_delete
from django.dispatch import receiver

import patch_sqlite_text_factory

import DurationField
from get_abbrev import get_abbrev

import re
import os
import math
import datetime
import base64
from django.utils.translation import ugettext_lazy as _
import utils
import random
import itertools
from collections import defaultdict
from TagFormat import getValidTagFormatStr, getTagFormatStr, getTagFromLicense, getLicenseFromTag
from CountryIOC import uci_country_codes_set, ioc_from_country, iso_uci_country_codes, country_from_ioc, province_codes
from large_delete_all import large_delete_all
from WriteLog import writeLog

def fixNullUpper( s ):
	if not s:
		return None
	s = (s or u'').strip()
	if s:
		return utils.removeDiacritic(s).upper().lstrip('0')
	else:
		return None

def getSrcStr( fname ):
	fileExtension = os.path.splitext(fname)[1]
	ftype = {
		'.png':		'png',
		'.gif':		'gif',
		'.jpeg':	'jpg',
		'.jpg':		'jpg',
	}[fileExtension.lower()]
	with open(fname, 'rb') as f:
		src = 'data:image/{};base64,{}'.format(ftype, base64.encodestring(f.read()))
	return src

KmToMiles = 0.621371192
MilesToKm = 1.0 / KmToMiles

#----------------------------------------------------------------------------------------
def getCopyName( ModelClass, cur_name ):
	suffix = u' - ['
	try:
		base_name = cur_name[:cur_name.rindex(suffix)]
	except:
		base_name = cur_name
	
	while 1:
		try:
			names = set( ModelClass.objects.filter(name__startswith=base_name).values_list('name', flat=True) )
		except:
			return cur_name
		
		iMax = 2
		for n in names:
			try:
				iMax = max( iMax, int(n[n.rindex('[')+1:-1]) + 1 )
			except:
				continue
		
		new_name = u'{}{}{}]'.format( base_name, suffix, iMax )
		if not ModelClass.objects.filter( name=new_name ).exists():
			return new_name
	
	return cur_name

#----------------------------------------------------------------------------------------
class SystemInfo(models.Model):
	tag_template = models.CharField( max_length = 24, verbose_name = _('Tag Template'), help_text=_("Template for generating EPC RFID tags from Database ID.") )
	
	tag_from_license = models.BooleanField( default = False, verbose_name = _("RFID Tag from License"),
			 help_text=_('Generate RFID tag from license (not database id)'))
	ID_CHOICES = [(i, u'{}'.format(i)) for i in xrange(32)]
	tag_from_license_id = models.PositiveSmallIntegerField( default=0, choices=ID_CHOICES, verbose_name=_('Identifier'),
		help_text=_('Identifier incorporated into the tag for additional recognition.') )

	RFID_SERVER_HOST_DEFAULT = 'localhost'
	RFID_SERVER_PORT_DEFAULT = 50111
	
	rfid_server_host = models.CharField( max_length = 32, default = RFID_SERVER_HOST_DEFAULT, verbose_name = _('RFID Reader Server Host')  )
	rfid_server_port = models.PositiveSmallIntegerField( default = RFID_SERVER_PORT_DEFAULT, verbose_name = _('RFID Reader Server Port') )
	
	reg_closure_minutes = models.IntegerField( default = -1, verbose_name = _('Reg Closure Minutes'), help_text=_('Minutes before race start to close registration for "reg" users.  Use -1 for None.') )
	
	exclude_empty_categories = models.BooleanField( default = True, verbose_name = _("Exclude Empty Categories from CrossMgr"),
			 help_text=_('Exclude empty categories from CrossMgr Excel'))
	
	reg_allow_add_multiple_categories = models.BooleanField( default = True, verbose_name = _('Allow "reg" to Add Participants to Multiple Categories'),
			 help_text=_('If True, reg staff can add participants to Multiple Categories (eg. race up a catgegory).  If False, only "super" can do so.'))
	
	license_code_regex = models.CharField( max_length = 160, blank = True, default = '', verbose_name = _('License Code Regex'), help_text=_('Must include a license_code field.  For example, "[^;]*;(?P&lt;license_code&gt;[^?]*).*"') )
	
	NO_PRINT_TAG, SERVER_PRINT_TAG, CLIENT_PRINT_TAG = 0, 1, 2
	print_tag_option = models.PositiveSmallIntegerField( default = NO_PRINT_TAG, verbose_name = _('Print Tag Option'), choices=(
			(NO_PRINT_TAG,_("No Bib Tag Print (Hide Print Bib Tag Button)")),
			(SERVER_PRINT_TAG,_("Print Bib Tag on Server (use command)")),
			(CLIENT_PRINT_TAG,_("Print Bib Tag on Client (print from browser)")),
		),
	)
	server_print_tag_cmd = models.CharField( max_length = 160, default = 'lpr "$1"', verbose_name = _('Cmd used to print Bib Tag (parameter is PDF file})')  )
	
	@classmethod
	def get_tag_template_default( cls ):
		rs = ''.join( '0123456789ABCDEF'[random.randint(1,15)] for i in xrange(4))
		tt = '{}######{:02}'.format( rs, datetime.datetime.now().year % 100 )
		return tt
	
	@classmethod
	def get_singleton( cls ):
		system_info = cls.objects.all().first()
		if system_info is None:
			system_info = cls( tag_template = cls.get_tag_template_default() )
			system_info.save()
		return system_info
	
	@classmethod
	def get_reg_closure_minutes( cls ):
		return cls.get_singleton().reg_closure_minutes
	
	@classmethod
	def get_exclude_empty_categories( cls ):
		return cls.get_singleton().exclude_empty_categories
	
	def save( self, *args, **kwargs ):
		self.tag_template = getValidTagFormatStr( self.tag_template )
		self.rfid_server_host = (self.rfid_server_host or self.RFID_SERVER_HOST_DEFAULT)
		self.rfid_server_port = (self.rfid_server_port or self.RFID_SERVER_PORT_DEFAULT)
		
		return super(SystemInfo, self).save( *args, **kwargs )
		
	class Meta:
		verbose_name = _('SystemInfo')

#----------------------------------------------------------------------------------------

class CategoryFormat(models.Model):
	name = models.CharField( max_length = 32, default = '', verbose_name = _('Name') )
	description = models.CharField( max_length = 80, blank = True, default = '', verbose_name = _('Description') )
	
	@transaction.atomic
	def make_copy( self ):
		categories = self.category_set.all()
		
		category_format_new = self
		category_format_new.pk = None
		category_format_new.save()
		
		for c in categories:
			c.make_copy( category_format_new )
		return category_format_new
	
	@property
	def next_category_seq( self ):
		try:
			return self.category_set.all().aggregate( Max('sequence') )['sequence__max'] + 1
		except:
			return 1
		
	def full_name( self ):
		return ','.join( [self.name, self.description] )
		
	def get_search_text( self ):
		return utils.get_search_text( [self.name, self.description] )
		
	def __unicode__( self ):
		return self.name
		
	class Meta:
		ordering = ['name']
		verbose_name = _('CategoryFormat')
		verbose_name_plural = _('CategoryFormats')

def init_sequence( Class, obj ):
	if not obj.sequence:
		obj.sequence = Class.objects.count() + 1
		
class Category(models.Model):
	format = models.ForeignKey( CategoryFormat, db_index = True )
	code = models.CharField( max_length=16, default='', verbose_name = _('Code') )
	GENDER_CHOICES = (
		(0, _('Men')),
		(1, _('Women')),
		(2, _('Open')),
	)
	gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, default = 0, verbose_name = _('Gender') )
	description = models.CharField( max_length = 80, default = '', blank = True, verbose_name = _('Description') )
	sequence = models.PositiveSmallIntegerField( default = 0, verbose_name = _('Sequence') )
	
	def save( self, *args, **kwargs ):
		init_sequence( Category, self )
		return super( Category, self ).save( *args, **kwargs )
	
	def make_copy( self, category_format ):
		category_new = self
		
		category_new.pk = None
		category_new.format = category_format
		category_new.save()
		return category_new
	
	def full_name( self ):
		return u', '.join( [self.code, self.get_gender_display(), self.description] )
		
	def get_search_text( self ):
		return utils.normalizeSearch(u' '.join( u'"{}"'.format(f) for f in [self.code, self.get_gender_display(), self.description] ) )
		
	def __unicode__( self ):
		return u'{} ({}) [{}]'.format(self.code, self.description, self.format.name)
		
	@property
	def code_gender( self ):
		return u'{} ({})'.format(self.code, self.get_gender_display())
	
	class Meta:
		verbose_name = _('Category')
		verbose_name_plural = _("Categories")
		ordering = ['sequence', '-gender', 'code']

#---------------------------------------------------------------------------------

class Discipline(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = 0 )
	
	def save( self, *args, **kwargs ):
		init_sequence( Discipline, self )
		return super( Discipline, self ).save( *args, **kwargs )
	
	def __unicode__( self ):
		return self.name
		
	class Meta:
		verbose_name = _('Discipline')
		verbose_name_plural = _('Disciplines')
		ordering = ['sequence', 'name']

class RaceClass(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = 0 )
	
	def save( self, *args, **kwargs ):
		init_sequence( RaceClass, self )
		return super( RaceClass, self ).save( *args, **kwargs )
	
	def __unicode__( self ):
		return self.name

	class Meta:
		verbose_name = _('Race Class')
		verbose_name_plural = _('Race Classes')
		ordering = ['sequence', 'name']

class NumberSet(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	sequence = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Sequence'), default = 0 )

	sponsor = models.CharField( max_length = 80, default = '', blank = True, verbose_name  = _('Sponsor') )
	description = models.CharField( max_length = 80, default = '', blank = True, verbose_name = _('Description') )
	
	def save( self, *args, **kwargs ):
		init_sequence( NumberSet, self )
		return super( NumberSet, self ).save( *args, **kwargs )
		
	def get_bib( self, competition, license_holder, category ):
		category_numbers = competition.get_category_numbers( category )
		if category_numbers:
			numbers = category_numbers.get_numbers()
			for bib in self.numbersetentry_set.filter(
					license_holder=license_holder, date_lost=None ).order_by('bib').values_list('bib', flat=True):
				if bib in numbers:
					return bib
		return None
		
	def assign_bib( self, license_holder, bib ):
		nse = self.numbersetentry_set.filter( license_holder=license_holder, bib=bib ).first()
		if nse:
			if nse.date_lost is not None:
				nse.date_lost = None
				nse.save()
		else:
			self.numbersetentry_set.filter( bib=bib ).exclude( license_holder=license_holder ).delete()
			NumberSetEntry( number_set=self, license_holder=license_holder, bib=bib ).save()
	
	def set_lost( self, bib ):
		self.numbersetentry_set.filter(bib=bib, date_lost=None).update( date_lost=datetime.date.today() )
	
	def return_to_pool( self, bib ):
		self.numbersetentry_set.filter( bib=bib ).delete()
	
	def __unicode__( self ):
		return self.name
	
	def normalize( self ):
		# Nulls sort to the beginning.  If we have a lost bib it will have a date_lost.
		# We want to keep lost entries, so we delete everything but the last one.
		duplicates = defaultdict( list )
		for nse in self.numbersetentry_set.order_by('bib', 'date_lost'):
			duplicates[nse.bib].append( nse.pk )
		for pks in duplicates.itervalues():
			if len(pks) > 1:
				NumberSetEntry.objects.filter( pk__in=pks[:-1] ).delete()
	
	class Meta:
		verbose_name = _('Number Set')
		verbose_name_plural = _('Number Sets')
		ordering = ['sequence']

#-------------------------------------------------------------------
class SeasonsPass(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	sequence = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Sequence'), default = 0 )

	def save( self, *args, **kwargs ):
		init_sequence( SeasonsPass, self )
		return super( SeasonsPass, self ).save( *args, **kwargs )
	
	def __unicode__( self ):
		return self.name
		
	def clone( self ):
		name_new = None
		for i in xrange(1, 1000):
			name_new = u'{} Copy({})'.format( self.name.split( ' Copy(' )[0], i )
			if not SeasonsPass.objects.filter( name=name_new ).exists():
				break
		seasons_pass_new = SeasonsPass( name=name_new )
		seasons_pass_new.save()
		with transaction.atomic():
			for sph in SeasonsPassHolder.objects.filter( seasons_pass=self ):
				sph.seasons_pass = seasons_pass_new
				sph.pk = None
				sph.save()
		return seasons_pass_new
	
	def add( self, license_holder ):
		try:
			SeasonsPassHolder(seasons_pass=self, license_holder=license_holder).save()
			return True
		except IntegrityError as e:
			return False
			
	def has_license_holder( self, license_holder ):
		return SeasonsPassHolder.objects.filter(seasons_pass=self, license_holder=license_holder).exists()
		
	def remove( self, license_holder ):
		SeasonsPassHolder.objects.filter(seasons_pass=self, license_holder=license_holder).delete()
	
	@property
	def holders_count( self ):
		return self.seasonspassholder_set.all().count()
	
	class Meta:
		verbose_name = _("Season's Pass")
		verbose_name_plural = _("Season's Passes")
		ordering = ['sequence']

class SeasonsPassHolder(models.Model):
	seasons_pass = models.ForeignKey( 'SeasonsPass', db_index = True, verbose_name = _("Season's Pass") )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True, verbose_name = _("LicenseHolder") )
	
	def __unicode__( self ):
		return u''.join( [unicode(self.seasons_pass), u': ', unicode(self.license_holder)] )
	
	class Meta:
		ordering = ['license_holder__search_text']
		unique_together = (
			('seasons_pass', 'license_holder'),
		)
		verbose_name = _("Season's Pass Holder")
		verbose_name_plural = _("Season's Pass Holders")

class ReportLabel( models.Model ):
	name = models.CharField( max_length = 32, verbose_name = _('Report Label'), help_text=_("Label used for reporting.") )
	sequence = models.PositiveSmallIntegerField( default = 0, verbose_name = _('Sequence') )
	
	def __unicode__( self ):
		return self.name
	
	class Meta:
		ordering = ['sequence']
		verbose_name = _("Report Label")
		verbose_name_plural = _("Report Labels")

class LegalEntity(models.Model):
	name = models.CharField( max_length=64, verbose_name=_('Name') )
	contact = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Contact') )
	email = models.EmailField( blank=True, verbose_name=_('Email') )
	phone = models.CharField( max_length=22, blank=True, default='', verbose_name=_('Phone') )
	website = models.CharField( max_length=255, blank=True, default='', verbose_name=_('Website') )
	
	waiver_expiry_date = models.DateField( default=datetime.date(1970,1,1), db_index=True, verbose_name=_('Waiver Expiry Date') )
	
	def __unicode__( self ):
		return self.name
	
	class Meta:
		ordering = ['name']
		verbose_name = _('LegalEntity')
		verbose_name_plural = _('LegalEntities')

#-------------------------------------------------------------------
class Competition(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	description = models.CharField( max_length = 80, default = '', blank = True, verbose_name=_('Description') )
	
	number_set = models.ForeignKey( NumberSet, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Number Set') )
	seasons_pass = models.ForeignKey( SeasonsPass, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Season's Pass") )
	
	city = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('City') )
	stateProv = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('StateProv') )
	country = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('Country') )
	
	category_format = models.ForeignKey(
		'CategoryFormat',
		verbose_name=_('Category Format') )
	
	organizer = models.CharField( max_length = 64, verbose_name=_('Organizer') )
	organizer_contact = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('Organizer Contact') )
	organizer_email = models.EmailField( blank = True, verbose_name=_('Organizer Email') )
	organizer_phone = models.CharField( max_length = 22, blank = True, default = '', verbose_name=_('Organizer Phone') )
	
	start_date = models.DateField( db_index = True, verbose_name=_('Start Date') )
	number_of_days = models.PositiveSmallIntegerField( default = 1, verbose_name = _('Number of Days') )
	
	discipline = models.ForeignKey( Discipline, verbose_name=_("Discipline") )
	race_class = models.ForeignKey( RaceClass, verbose_name=_("Race Class") )
	
	using_tags = models.BooleanField( default = False, verbose_name = _("Using Tags/Chip Reader") )
	use_existing_tags = models.BooleanField( default = True, verbose_name = _("Use Competitor's Existing Tags") )
	
	DISTANCE_UNIT_CHOICES = (
		(0, _('km')),
		(1, _('miles')),
	)
	distance_unit = models.PositiveSmallIntegerField(choices=DISTANCE_UNIT_CHOICES, default = 0, verbose_name = _('Distance Unit') )
	
	ftp_host = models.CharField( max_length = 80, default = '', blank = True, verbose_name=_('FTP Host') )
	ftp_user = models.CharField( max_length = 80, default = '', blank = True, verbose_name=_('FTP User') )
	ftp_password = models.CharField( max_length = 64, default = '', blank = True, verbose_name=_('FTP Password') )
	ftp_path = models.CharField( max_length = 256, default = '', blank = True, verbose_name=_('FTP Path') )
	
	ftp_upload_during_race = models.BooleanField( default = False, verbose_name = _("Live FTP Update During Race") )
	
	show_signature = models.BooleanField( default = True, verbose_name = _("Show Signature in Participant Edit Screen") )
	
	ga_tracking_id = models.CharField( max_length = 20, default = '', blank = True, verbose_name=_('Google Analytics Tracking ID') )
	
	report_labels = models.ManyToManyField( ReportLabel, blank=True, verbose_name = _('Report Labels') )
	
	legal_entity = models.ForeignKey( LegalEntity, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Legal Entity') )
	
	RECURRING_CHOICES = (
		( 0, '-'),
		( 7, _('Every Week')),
		(14, _('Every 2 Weeks')),
		(21, _('Every 3 Weeks')),
		(28, _('Every 4 Weeks')),
	)
	recurring = models.PositiveSmallIntegerField(choices=RECURRING_CHOICES, default=0, verbose_name=_('Recurring') )
	
	@property
	def speed_unit_display( self ):
		return 'km/h' if self.distance_unit == 0 else 'mph'
	
	@property
	def report_labels_text( self ):
		return u', '.join( r.name for r in self.report_labels.all() )
	
	@property
	def event_types_text( self ):
		types = []
		if EventMassStart.objects.filter( competition=self ).exists():
			types.append( _('MS') )
		if EventTT.objects.filter( competition=self ).exists():
			if types:
				types.append( ',' )
			types.append( _('TT') )
		if types:
			types = ['('] + types + [')']
			return string_concat( *types )
		return ''
	
	def to_local_speed( self, kmh ):
		return kmh if self.distance_unit == 0 else kmh * 0.621371
		
	def to_kmh( self, speed ):
		return speed if self.distance_unit == 0 else speed / 0.621371
	
	def save(self, *args, **kwargs):
		''' If the start_date has changed, automatically update all the event dates too. '''
		if self.pk:
			try:
				competition_original = Competition.objects.get( pk = self.pk )
			except Exception as e:
				competition_original = None
			if competition_original and competition_original.start_date != self.start_date:
				time_delta = (
					datetime.datetime.combine(self.start_date, datetime.time(0,0,0)) -
					datetime.datetime.combine(competition_original.start_date, datetime.time(0,0,0))
				)
				self.adjust_event_times( time_delta )
			
		return super(Competition, self).save(*args, **kwargs)
	
	@transaction.atomic
	def make_copy( self ):
		category_numbers = self.categorynumbers_set.all()
		event_mass_starts = self.eventmassstart_set.all()
		event_tts = self.eventtt_set.all()
		report_labels = list( self.report_labels.all() )
	
		start_date_old, start_date_new = self.start_date, datetime.date.today()
		competition_new = self
		competition_new.pk = None
		competition_new.start_date = start_date_new
		competition_new.save()
		
		for cn in category_numbers:
			cn.make_copy( competition_new )
		for e in event_mass_starts:
			e.make_copy( competition_new, start_date_old, start_date_new )
		for e in event_tts:
			e.make_copy( competition_new, start_date_old, start_date_new )
		
		if report_labels:
			competition_new.report_labels.add( *report_labels )
		
		return competition_new
		
	def adjust_event_times( self, time_delta ):
		for e in self.get_events():
			e.date_time += time_delta
			e.save()
	
	@property
	def has_waiver( self ):
		return self.legal_entity and self.legal_entity.waiver_expiry_date > datetime.date(1970,1,1)
	
	@property
	def finish_date( self ):
		return self.start_date + datetime.timedelta( days = self.number_of_days - 1 )
		
	@property
	def date_range_str( self ):
		sd = self.start_date
		ed = self.finish_date
		if sd == ed:
			return sd.strftime('%b %d, %Y')
		if sd.month == ed.month and sd.year == ed.year:
			return u'{}-{}'.format( sd.strftime('%b %d'), ed.strftime('%d, %Y') )
		if sd.year == ed.year:
			return u'{}-{}'.format( sd.strftime('%b %d'), ed.strftime('%b %d, %Y') )
		return u'{}-{}'.format( sd.strftime('%b %d, %Y'), ed.strftime('%b %d, %Y') )
	
	@property
	def has_optional_events( self ):
		return (
			EventMassStart.objects.filter(competition=self, optional=True).exists() or
			EventTT.objects.filter(competition=self, optional=True).exists()
		)
		
	def add_all_participants_to_default_events( self ):
		ParticipantOption.objects.filter( competition=self ).delete()

		default_events = [event for event in self.get_events() if event.optional and event.select_by_default]
		if not default_events:
			return
		
		category_event_ids = defaultdict( set )
		for event in default_events:
			for category in event.get_categories():
				category_event_ids[category.pk].add( event.option_id )

		options = list(
			itertools.chain.from_iterable(
				(ParticipantOption( competition=self, participant=participant, option_id=option_id )
					for option_id in category_event_ids[participant.category.pk])
				for participant in Participant.objects.filter(
					competition=self, role=Participant.Competitor, category__isnull=False
				)
			)
		)
		ParticipantOption.objects.bulk_create( options )
	
	def full_name( self ):
		return ' '.join( [self.name, self.organizer] )
		
	def get_search_text( self ):
		return utils.get_search_text( [self.name, self.organizer] )
	
	def get_events_mass_start( self ):
		return EventMassStart.objects.filter(competition = self).order_by('date_time')
		
	def get_events_tt( self ):
		return EventTT.objects.filter(competition = self).order_by('date_time')
		
	def get_events( self ):
		return list(self.get_events_mass_start()) + list(self.get_events_tt())
		
	def get_categories( self ):
		return Category.objects.filter( format=self.category_format )
		
	def get_teams( self ):
		return Team.objects.filter( pk__in=set(
				Participant.objects.filter(competition=self).exclude(team__isnull=True).values_list('team', flat=True)
			)
		)
	
	#----------------------------------------------------------------------------------------------------

	def get_categories_with_numbers( self ):
		category_lookup = set( Category.objects.filter(format = self.category_format).values_list('pk', flat=True) )
		categories = []
		for cn in self.categorynumbers_set.all():
			categories.extend( list(c for c in cn.categories.all() if c.pk in category_lookup) )
		return sorted( set(categories), key = lambda c: c.sequence )
		return categories
	
	def get_categories_without_numbers( self ):
		categories_all = set( Category.objects.filter(format = self.category_format) )
		categories_with_numbers = set( self.get_categories_with_numbers() )
		categories_without_numbers = categories_all - categories_with_numbers
		return sorted( categories_without_numbers, key = lambda c: c.sequence )
	
	def get_category_numbers( self, category ):
		return CategoryNumbers.objects.filter( competition=self, categories__in=[category] ).first()
	
	#----------------------------------------------------------------------------------------------------

	def competition_age( self, license_holder ):
		# For cyclocross races between September and December,
		# use the next year as the competition age, not the current year.
		age = self.start_date.year - license_holder.date_of_birth.year
		if 'cyclo' in self.discipline.name.lower() and 9 <= self.start_date.month <= 12:
			age += 1
		return age
	
	def get_participant_events( self, participant ):
		participant_events = []
		if not participant.category:
			return participant_events
		for events in (self.eventmassstart_set.all(), self.eventtt_set.all()):
			for event in events:
				if event.could_participate(participant):
					participant_events.append( (event, event.is_optional, event.is_participating(participant)) )
		return participant_events
		
	def has_any_events( self, participant ):
		if not participant.category:
			return False
		if (
			Wave.objects.filter(
				event__competition=self, event__optional=False, categories__in=[participant.category]).exists() or 
			WaveTT.objects.filter(
				event__competition=self, event__optional=False, categories__in=[participant.category]).exists()
			):
			return True
		for events in (self.eventmassstart_set.filter(optional=True), self.eventtt_set.filter(optional=True)):
			for event in events:
				if event.could_participate(participant) and event.is_participating(participant):
					return True
		return False
	
	def get_participants( self ):
		return Participant.objects.filter( competition=self )
		
	def has_participants( self ):
		return self.get_participants().exists()
		
	def get_available_categories( self, license_holder, gender=None, participant_exclude=None ):
		categories_remaining = Category.objects.filter( format=self.category_format )
		if gender is None:
			gender = license_holder.gender
		if gender != -1:
			categories_remaining = categories_remaining.filter( Q(gender=2) | Q(gender=gender) )
		
		participants = list( Participant.objects.filter(competition=self, role=Participant.Competitor, license_holder=license_holder) )
		if not participants:
			return list(categories_remaining)
		
		# Only return categories that are not in the same event.
		categories_remaining = set( categories_remaining )
		
		if participant_exclude:
			categories_remaining.discard( participant_exclude.category )
		
		for e in self.get_events():
			for p in participants:
				if p != participant_exclude and e.is_participating(p):
					categories_remaining -= set( e.get_categories_with_wave() )
		return sorted( set(categories_remaining), key=lambda c: c.sequence )
		
	def is_category_conflict( self, categories ):
		if len(categories) <= 1:
			return False
		for e in self.get_events():
			event_categories = set( e.get_categories_with_wave() )
			for a in categories:
				if a in event_categories:
					for b in categories:
						if a != b and b in event_categories:
							return True
		return False
	
	@transaction.atomic
	def auto_generate_missing_tags( self ):
		participants_changed = []
		for participant in self.get_participants():
			if participant.tag:
				continue
			license_holder = participant.license_holder
			if not license_holder.existing_tag:
				license_holder.existing_tag = license_holder.get_unique_tag()
				license_holder.save()
			participant.tag = license_holder.existing_tag
			participant.save()
			participants_changed.append( participant )
		
		participants_changed.sort( key=lambda p: (p.bib or 99999999, p.license_holder.search_text) ) 
		return participants_changed
	
	def apply_number_set( self ):
		participants_changed = []
		if self.number_set:
			self.number_set.normalize()
			
			participants = self.get_participants().filter( role=Participant.Competitor )
			
			category_nums = {}
			for category_numbers in CategoryNumbers.objects.filter( competition=self ):
				for c in category_numbers.categories.all():
					category_nums[c.pk] = category_numbers.get_numbers()
			
			bib_last = { pk:bib for pk, bib in participants.values_list('pk', 'bib') }
			participants.update( bib=None )
			
			nses = defaultdict( list )
			for pk, bib in NumberSetEntry.objects.filter(
					number_set=self.number_set, date_lost=None).values_list(
					'license_holder__pk', 'bib'):
				nses[pk].append( bib )
				
			for bibs in nses.itervalues():
				bibs.sort()
			
			with transaction.atomic():
				for p in participants:
					bib_category = None
					if p.category:
						for bib in nses[p.license_holder.pk]:
							if bib in category_nums[p.category.pk]:
								bib_category = bib
								break
					if p.bib != bib_category:
						p.bib = bib_category
						p.save()
					if bib_last[p.pk] != p.bib:
						participants_changed.append( p )
		
		participants_changed.sort( key=lambda p: (p.bib or 99999999, p.license_holder.search_text) ) 
		return participants_changed
	
	@transaction.atomic
	def initialize_number_set( self ):
		if self.number_set:
			large_delete_all( NumberSetEntry, Q(number_set=self.number_set) )
			NumberSetEntry.objects.bulk_create( [
					NumberSetEntry(number_set=self.number_set, license_holder=participant.license_holder, bib=participant.bib, date_lost=None)
						for participant in self.get_participants().filter(role=Participant.Competitor) if participant.bib
				]
			)
			self.number_set.normalize()
	
	class Meta:
		verbose_name = _('Competition')
		verbose_name_plural = _('Competitions')
		ordering = ['-start_date', 'name']

class CategoryNumbers( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True )
	categories = models.ManyToManyField( Category )
	range_str = models.TextField( default = '1-99,120-129,-50-60,181,-87', verbose_name=_('Range') )
	
	numCache = None
	valid_chars = set( u'0123456789,-' )
	numMax = 99999
	
	@property
	def category_list( self ):
		return u', '.join( c.code_gender for c in self.get_category_list() )
	
	def get_category_list( self ):
		return sorted( self.categories.all(), key = lambda c: c.sequence )
	
	def get_key( self ):
		try:
			return min( c.sequence for c in self.categories.all() )
		except ValueError:
			return -1
	
	def make_copy( self, competition_new ):
		categories = self.categories.all()
		
		category_numbers_new = self
		category_numbers_new.pk = None
		category_numbers_new.competition = competition_new
		category_numbers_new.save()
		
		category_numbers_new.categories = categories
		return category_numbers_new
	
	def normalize( self ):
		# Normalize the input.
		r = self.range_str.replace( u' ', u',' ).replace( u'\n', u',' )
		r = u''.join( v for v in r if v in self.valid_chars )
		while 1:
			rNew = r.replace( ',,', ',' ).replace( '--', '-' ).replace( '-,', ',' )
			if rNew == r:
				break
			r = rNew
		if r.startswith( ',' ):
			r = r[1:]
		while r.endswith( ',' ) or r.endswith( '-' ):
			r = r[:-1]
		
		pairs = []
		for p in r.split( u',' ):
			p = p.strip()
			if p.startswith( '-' ):
				exclude = u'-'
				p = p[1:]
			else:
				exclude = u''
				
			pair = p.split( u'-' )
			if len(pair) == 1:
				try:
					n = int(pair[0])
				except:
					continue
				pairs.append( exclude + unicode(n) )
			elif len(pair) >= 2:
				try:
					nBegin = int(pair[0])
				except:
					continue
				try:
					nEnd = int(pair[1])
				except:
					continue
				nBegin = min( nBegin, self.numMax )
				nEnd = min( max(nBegin,nEnd), self.numMax )
				pairs.append( exclude + unicode(nBegin) + u'-' + unicode(nEnd) )
		
		self.range_str = u', '.join( pairs )
	
	def getNumbersWorker( self ):
		self.normalize()
		
		include = set()
		for p in self.range_str.split( ',' ):
			p = p.strip()
			if not p:
				continue
			
			if p.startswith( '-' ):
				exclude = True
				p = p[1:]
			else:
				exclude = False
				
			pair = p.split( '-' )
			if len(pair) == 1:
				n = max(1, int(pair[0]))
				if exclude:
					include.discard( n )
				else:
					include.add( n )
			else:
				nBegin, nEnd = [int(v) for v in pair[:2]]
				nBegin, nEnd = max(nBegin, 1), min(nEnd, 99999)
				if exclude:
					include.difference_update( xrange(nBegin, nEnd+1) )
				else:
					include.update( xrange(nBegin, nEnd+1) )
		self.numbers = include
		return include
	
	def get_numbers( self ):
		if self.numCache is None or getattr(self, 'range_str_cache', None) != self.range_str:
			self.numCache = self.getNumbersWorker()
			self.range_str_cache = self.range_str
		return self.numCache
	
	def __contains__( self, n ):
		return n in self.get_numbers()
		
	def add_bib( self, n ):
		if n not in self:
			self.range_str += u', {}'.format( n )
			
	def remove_bib( self, n ):
		if n in self:
			self.range_str += u', -{}'.format( n )
		
	def save(self, *args, **kwargs):
		self.normalize()
		return super(CategoryNumbers, self).save( *args, **kwargs )
		
	class Meta:
		verbose_name = _('CategoryNumbers')
		verbose_name_plural = _('CategoriesNumbers')

class Event( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True )
	name = models.CharField( max_length = 80, verbose_name=_('Name') )
	date_time = models.DateTimeField( db_index = True, verbose_name=_('Date Time') )
	
	EVENT_TYPE_CHOICES = (
		(0, _('Mass Start')),
		(1, _('Time Trial')),
		#(2, _('Sprint')),
	)
	event_type = models.PositiveSmallIntegerField( choices=EVENT_TYPE_CHOICES, default = 0, verbose_name = ('Event Type') )
	
	@property
	def edit_link( self ):
		return '{}/{}'.format( ['EventMassStart', 'EventTT', 'EventSprint'][self.event_type], self.pk )
	
	optional = models.BooleanField( default=False, verbose_name=_('Optional'),
		help_text=_('Allows Participants to choose to enter the Event.  Otherwise the Event is included for all participants.') )
	option_id = models.PositiveIntegerField( default=0, verbose_name = _('Option Id') )
	select_by_default = models.BooleanField( default=False, verbose_name=_('Select by Default'),
		help_text=_('If the Event is "Optional", and "Select by Default", Participants will be automatically added to the Event (but can opt-out later).') )
	
	RFID_OPTION_CHOICES = (
		(0, _('Manual Start: Collect every chip. Does NOT restart race clock on first read.')),
		(1, _('Automatic Start: Reset start clock on first tag read.  All riders get the start time of the first read.')),
		(2, _('Manual Start: Skip first tag read for all riders.  Required when start run-up passes the finish line.')),
	)
	rfid_option = models.PositiveIntegerField( choices=RFID_OPTION_CHOICES, default=1, verbose_name = _('RFID Option') )
	
	road_race_finish_times = models.BooleanField( default = False, verbose_name = _("Road Race Finish Times"),
		help_text = _("Ignore decimals, groups get same time") )
	
	note = models.TextField( null=True, blank=True, verbose_name=_('Note') )
	
	dnsNoData = models.BooleanField( default=True, verbose_name = _("Show Participants with no race data as DNS"), )
	
	@property
	def note_html( self ):
		return mark_safe( u'<br/>'.join( self.note.split(u'\n') ) ) if self.note else u''
	
	@property
	def is_optional( self ):
		return self.option_id != 0
	
	def save( self, *args, **kwargs ):
		if not self.optional and self.option_id:
			ParticipantOption.delete_option_id( self.competition, self.option_id )
			self.option_id = 0
		super( Event, self ).save( *args, **kwargs )
		if self.optional and not self.option_id:
			ParticipantOption.set_event_option_id( self.competition, self )
	
	def get_wave_set( self ):
		try:
			return self.wave_set
		except AttributeError:
			return self.wavett_set
			
	def get_categories( self ):
		categories = set()
		for w in self.get_wave_set().all(): 
			categories |= set( w.categories.all() )
		return sorted( categories, key = lambda c: c.sequence )

	def reg_is_late( self, reg_closure_minutes, registration_timestamp ):
		if reg_closure_minutes < 0:
			return False
		delta = self.date_time - registration_timestamp
		return delta.total_seconds()/60.0 < reg_closure_minutes
	
	def make_copy( self, competition_new, start_date_old, start_date_new ):
		time_diff = self.date_time - datetime.datetime.combine(
			start_date_old, datetime.time(0,0,0)
		).replace(tzinfo = get_default_timezone())
		waves = self.get_wave_set().all()
		
		event_mass_start_new = self
		event_mass_start_new.pk = None
		event_mass_start_new.competition = competition_new
		event_mass_start_new.date_time = datetime.datetime.combine(
			start_date_new, datetime.time(0,0,0)).replace(tzinfo = get_default_timezone()) + time_diff
		event_mass_start_new.option_id = 0		# Ensure the option_id gets reset if necessary.
		event_mass_start_new.save()
		
		for w in waves:
			w.make_copy( event_mass_start_new )
		return event_mass_start_new
	
	def get_duplicate_bibs( self ):
		duplicates = []
		for w in self.get_wave_set().all():
			bibParticipant = {}
			for c in w.categories.all():
				for p in Participant.objects.filter( competition=self.competition, role=Participant.Competitor, category=c, bib__isnull=False ):
					if p.bib in bibParticipant:
						duplicates.append( string_concat(
							w.name, ': ', bibParticipant[p.bib].name,
							' ( ', bibParticipant[p.bib].category.code, ') and ',
							p.name, ' (', p.category.code, ' ) ', _('have duplicate Bib'), p.bib) )
					else:
						bibParticipant[p.bib] = p
		return duplicates
		
	#----------------------------------------------------------------------------------------------------
	
	def get_potential_duplicate_bibs( self ):
		categories = set()
		for w in self.get_wave_set().all():
			categories |= set( w.categories.all() )
				
		category_numbers = set()
		for c in categories:
			for cn in CategoryNumbers.objects.filter( competition=self.competition, categories__in=[c] ):
				category_numbers.add( cn )
		
		potential_duplicates = []
		category_numbers = list( category_numbers )
		for i, cnLeft in enumerate(category_numbers):
			numbersLeft = cnLeft.get_numbers()
			for cnRight in category_numbers[i+1:]:
				numbersRight = cnRight.get_numbers()
				numbersConflict = numbersLeft & numbersRight
				if numbersConflict:
					potential_duplicates.append( (
						u', '.join( c.code for c in cnLeft.categories.all() ),
						u', '.join( c.code for c in cnRight.categories.all() ),
						sorted(numbersConflict)
					))						
		return potential_duplicates

	def get_categories_with_wave( self ):
		category_lookup = set( Category.objects.filter(format = self.competition.category_format).values_list('pk', flat=True) )
		categories = []
		for wave in self.get_wave_set().all():
			categories.extend( list(c for c in wave.categories.all() if c.pk in category_lookup) )
		return sorted( set(categories), key = lambda c: c.sequence )
	
	def get_categories_without_wave( self ):
		categories_all = set( Category.objects.filter(format = self.competition.category_format) )
		categories_with_wave = set( self.get_categories_with_wave() )
		categories_without_wave = categories_all - categories_with_wave
		return sorted( categories_without_wave, key = lambda c: c.sequence )
	
	def get_late_reg_exists( self ):
		return any( w.get_late_reg().exists() for w in self.get_wave_set().all() )
		
	def could_participate( self, participant ):
		return participant.category and any( w.could_participate(participant) for w in self.get_wave_set().all() )
		
	def is_participating( self, participant ):
		return participant.category and any( w.is_participating(participant) for w in self.get_wave_set().all() )
		
	def get_json( self ):
		server_date_time = timezone.localtime(self.date_time)
		return {
			'name':	self.name,
			'pk': self.pk,
			'competition_name': self.competition.name,
			'date_time': unicode(server_date_time),
			'event_type': self.event_type,
			'optional':	self.optional,
			'select_by_default': self.select_by_default,
			'participant_count': self.get_participant_count(),
			'waves': [w.get_json() for w in self.get_wave_set().all()],
		}
		
	@property
	def wave_text( self ):
		return u', '.join( u'{} ({})'.format(w.name, w.category_text) for w in self.get_wave_set().all() )
	
	@property
	def wave_text_line_html( self ):
		return u', '.join( u'<strong>{}</strong> {}'.format(w.name, w.category_text) for w in self.get_wave_set().all() )
	
	@property
	def wave_text_html( self ):
		return u'<ol><li>' + u'</li><li>'.join( u'<strong>{}, {}</strong><br/>{}'.format(
			w.name, w.get_details_html(True), 
			w.category_count_html
		) for w in self.get_wave_set().all() ) + u'</li></ol>'
	
	'''
	def get_participants( self ):
		participants = set()
		for w in self.get_wave_set().all():
			participants |= set( w.get_participants_unsorted().select_related('license_holder','team') )
		return participants
		
	def has_participants( self ):
		return any( w.get_participants_unsorted().exists() for w in self.get_wave_set().all() )
	'''
	
	def get_participants( self ):
		categories = []
		map( categories.extend, (w.categories.all().values_list('pk', flat=True) for w in self.get_wave_set().all()) )
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=categories,
			).select_related('license_holder','team')
		else:
			return Participant.objects.filter(
				pk__in=ParticipantOption.objects.filter(
					competition=self.competition,
					option_id=self.option_id,
					participant__role=Participant.Competitor,
					participant__competition=self.competition,
					participant__category__in=categories,
				).values_list('participant__pk', flat=True)
			).select_related('license_holder','team')

	def has_participants( self ):
		categories = []
		map( categories.extend, (w.categories.all().values_list('pk', flat=True) for w in self.get_wave_set().all()) )
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=categories,
			).exists()
		else:
			return ParticipantOption.objects.filter(
				competition=self.competition,
				option_id=self.option_id,
				participant__role=Participant.Competitor,
				participant__competition=self.competition,
				participant__category__in=categories,
			).exists()
		
	def get_participant_count( self ):
		categories = []
		map( categories.extend, (w.categories.all().values_list('pk', flat=True) for w in self.get_wave_set().all()) )
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=categories,
			).count()
		else:
			return ParticipantOption.objects.filter(
				competition=self.competition,
				option_id=self.option_id,
				participant__role=Participant.Competitor,
				participant__competition=self.competition,
				participant__category__in=categories,
			).count()

	def get_ineligible( self ):
		return self.get_participants().filter( license_holder__eligible=False ).order_by('license_holder__search_text')
			
	def __unicode__( self ):
		return u'{}, {} ({})'.format(self.date_time, self.name, self.competition.name)
	
	@property
	def short_name( self ):
		return u'{} ({})'.format( self.name, {0:_('Mass'), 1:_('TT')}.get(self.event_type,u'') )
	
	def apply_optional_participants( self ):
		if not self.optional:
			return
			
		ParticipantOption.objects.filter( competition=self.competition, option_id=self.option_id ).delete()

		if self.select_by_default:
			options = list(
				ParticipantOption( competition=self.competition, participant=participant, option_id=self.option_id )
					for participant in Participant.objects.filter(
						competition=self.competition, role=Participant.Competitor, category__in=self.get_categories()
					)
			)
			ParticipantOption.objects.bulk_create( options )
	
	class Meta:
		verbose_name = _('Event')
		verbose_name_plural = _('Events')
		ordering = ['date_time']
		abstract = True

#---------------------------------------------------------------------------------------------------------

class EventMassStart( Event ):
	
	win_and_out = models.BooleanField( default = False, verbose_name = _("Win and Out") )

	class Meta:
		verbose_name = _('Mass Start Event')
		verbose_name_plural = _('Mass Starts Event')

class WaveBase( models.Model ):
	name = models.CharField( max_length = 32 )
	categories = models.ManyToManyField( Category, verbose_name = _('Categories') )
	
	distance = models.FloatField( null = True, blank = True, verbose_name = _('Distance') )
	laps = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Laps') )
	
	max_participants = models.PositiveIntegerField( null = True, blank = True, verbose_name = _('Max Participants') )
	
	@property
	def distance_unit( self ):
		return self.event.competition.get_distance_unit_display() if self.event else ''
	
	def get_category_format( self ):
		return self.event.competition.category_format
	
	def make_copy( self, event_new ):
		categories = self.categories.all()
		wave_new = self
		wave_new.pk = None
		wave_new.event = event_new
		wave_new.save()
		wave_new.categories = categories
		return wave_new
	
	def get_potential_duplicate_bibs( self ):
		if not self.id:
			return []
		competition = self.event.competition
		
		other_categories = set()
		my_categories = set()
		
		for w in self.event.get_wave_set().all():
			if w != self:
				other_categories |= set( w.categories.all() )
			else:
				my_categories |= set( w.categories.all() )
		
		other_category_numbers = set()
		my_category_numbers = set()
		for cn in self.event.competition.categorynumbers_set.all():
			categories_cur = list( cn.categories.all() )
			if any( c in other_categories for c in categories_cur ):
				other_category_numbers.add( cn )
			if any( c in my_categories for c in categories_cur ):
				my_category_numbers.add( cn )
		
		other_bibs = set.union( *[c.get_numbers() for c in other_category_numbers] ) if other_category_numbers else set()
		my_bibs = set.union( *[c.get_numbers() for c in my_category_numbers] ) if my_category_numbers else set()
		
		return sorted( other_bibs & my_bibs )
	
	def get_participant_options( self ):
		return ParticipantOption.objects.filter(
			competition=self.event.competition,
			option_id=self.event.option_id,
			participant__role=Participant.Competitor,
			participant__competition=self.event.competition,
			participant__category__in=self.categories.all(),
		)
		
	def get_participants_unsorted( self ):
		if not self.event.option_id:
			return Participant.objects.filter(
				competition=self.event.competition,
				role=Participant.Competitor,
				category__in=self.categories.all(),
			)
		else:
			return Participant.objects.filter( pk__in=self.get_participant_options().values_list('participant__pk', flat=True) )
	
	def get_participant_count( self ):
		if not self.event.option_id:
			return Participant.objects.filter(
				competition=self.event.competition,
				role=Participant.Competitor,
				category__in=self.categories.all(),
			).count()
		else:
			return self.get_participant_options().count()
	
	def get_participants( self ):
		return self.get_participants_unsorted().select_related('license_holder','team').order_by('bib')
	
	@property
	def spots_remaining( self ):
		return None if self.max_participants is None else max(0, self.max_participants - get_participant_count())
	
	@property
	def is_full( self ):
		return self.max_participants is not None and self.spots_remaining <= 0
		
	def get_starters_str( self ):
		count = self.get_participant_count()
		if self.max_participants is None:
			return '{}'.format( count )
		else:
			percent = 100.0 * float(count)/float(self.max_participants)
			return '({:.0f}%) {}/{}'.format( percent, count, self.max_participants )
	
	def could_participate( self, participant ):
		return participant.category and self.categories.filter(pk=participant.category.pk).exists()
	
	def is_participating( self, participant ):
		return (not self.event.option_id or
					ParticipantOption.objects.filter(
						competition=self.event.competition,
						participant=participant,
						option_id=self.event.option_id).exists()) and self.could_participate(participant)
	
	def reg_is_late( self, reg_closure_minutes, registration_timestamp ):
		return self.event.reg_is_late( reg_closure_minutes, registration_timestamp )
	
	def get_late_reg( self ):
		latest_reg_timestamp = self.event.date_time - datetime.timedelta( seconds=SystemInfo.get_reg_closure_minutes()*60 )
		return self.get_participants_unsorted().filter( registration_timestamp__gt=latest_reg_timestamp )
	
	def get_late_reg_set( self ):
		return set( self.get_late_reg() )
	
	def get_late_reg_count( self ):
		return self.get_late_reg().count()
		
	def get_json( self ):
		category_count = self.get_category_count()
		return {
			'name': self.name,
			'categories': [{'name':c.full_name(), 'participant_count':cc} for c, cc in category_count],
			'participant_count': sum(cc[1] for cc in category_count),
		}
	
	@property
	def category_text( self ):
		return u', '.join( category.code_gender for category in sorted(self.categories.all(), key=lambda c: c.sequence) )
	
	def get_category_count( self ):
		category_count = defaultdict( int )
		for p in self.get_participants_unsorted():
			category_count[p.category] += 1
		return [(category, category_count[category]) for category in sorted(self.categories.all(), key=lambda c: c.sequence)]
	
	@property
	def category_count_text( self ):
		return u', '.join( u'{} {}'.format(category.code_gender, category_count) for category, category_count in self.get_category_count() )
	
	@property
	def category_count_html( self ):
		return u', '.join( u'{} {}'.format(category.code_gender, category_count).replace(u' ', u'&nbsp;') for category, category_count in self.get_category_count() )
	
	@property
	def category_text_html( self ):
		return u'<ol><li>' + u'</li><li>'.join( category.code_gender for category in sorted(self.categories.all(), key=lambda c: c.sequence) ) + u'</li></ol>'
		
	def get_details_html( self, include_starters=False ):
		distance = None
		if self.distance:
			if self.laps:
				distance = self.distance * self.laps
			else:
				distance = self.distance
		return u', '.join( v for v in [
			u'{}:&nbsp;{}'.format(_('Offset'), self.start_offset) if include_starters and hasattr(self,'start_offset') else None,
			u'{:.2f}&nbsp;{}'.format(distance, self.distance_unit) if distance else None,
			u'{}&nbsp;{}'.format(self.laps, _('laps') if self.laps != 1 else _('lap')) if self.laps else None,
			u'{}&nbsp;{}'.format(self.minutes, _('min')) if getattr(self, 'minutes', None) else None,
			u'{}:&nbsp;{}'.format(_('Strs'), self.get_starters_str().replace(' ', '&nbsp;')) if include_starters else None,
		] if v )
	
	class Meta:
		verbose_name = _('Wave Base')
		verbose_name_plural = _('Wave Bases')
		abstract = True

class Wave( WaveBase ):
	event = models.ForeignKey( EventMassStart, db_index = True )
	start_offset = DurationField.DurationField( default = 0, verbose_name = _('Start Offset') )
	
	minutes = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Race Minutes') )
	
	def get_json( self ):
		js = super(Wave, self).get_json()
		try:
			seconds = self.start_offset.total_seconds()
		except:
			seconds = self.start_offset
		js['start_offset'] = DurationField.format_seconds( seconds )
		return js
	
	def get_start_time( self ):
		try:
			return self.event.date_time + self.start_offset
		except TypeError:
			return self.event.date_time + datetime.timedelta(self.start_offset)
	
	class Meta:
		verbose_name = _('Wave')
		verbose_name_plural = _('Waves')
		ordering = ['start_offset', 'name']

class WaveCallup( models.Model ):
	wave = models.ForeignKey( Wave, db_index = True )
	participant = models.ForeignKey( 'Participant', db_index = True )
	order = models.PositiveSmallIntegerField( blank = True, default = 9999, verbose_name = _('Callup Order') )
	
	class Meta:
		verbose_name = _('WaveCallup')
		verbose_name_plural = _('WaveCallups')
		ordering = ['order']
	
#-------------------------------------------------------------------------------------
class Team(models.Model):
	name = models.CharField( max_length = 64, db_index = True, verbose_name = _('Name') )
	team_code = models.CharField( max_length = 3, blank = True, db_index = True, verbose_name = _('Team Code') )
	TYPE_CHOICES = (
		(0, _('Club')),
		(1, _('Regional')),
		(2, _('Mixed')),
		(3, _('National')),
		(4, _('UCI Women')),
		(5, _('UCI Continental')),
		(6, _('UCI Pro Continental')),
		(7, _('UCI Pro')),
	)
	team_type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default = 0, verbose_name = _('Type') )
	nation_code = models.CharField( max_length=3, blank = True, default='', verbose_name = _('Nation Code') )
	
	active = models.BooleanField( default = True, verbose_name = _('Active') )
	
	was_team = models.OneToOneField('self', blank=True, null=True, on_delete=models.SET_NULL,
					related_name='is_now_team', verbose_name = _('Was Team'))
					
	SearchTextLength = 80
	search_text = models.CharField( max_length=SearchTextLength, blank=True, default='', db_index=True )

	def save( self, *args, **kwargs ):
		self.search_text = self.get_search_text()[:self.SearchTextLength]
		return super(Team, self).save( *args, **kwargs )
	
	def full_name( self ):
		fields = [self.name, self.team_code, self.get_team_type_display(), self.nation_code]
		return u', '.join( f for f in fields if f )
	
	def get_search_text( self ):
		return utils.get_search_text( [self.name, self.team_code, self.get_team_type_display(), self.nation_code] )
	
	def short_name( self ):
		return self.name
		
	def unicode( self ):
		return u'{}, {}'.format(self.name, self.team_type_display())
	
	class Meta:
		verbose_name = _('Team')
		verbose_name_plural = _('Teams')
		ordering = ['search_text']

rePostalCode = re.compile('^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$')
def validate_postal_code( postal ):
	postal = (postal or '').replace(' ', '').upper()
	return postal[0:3] + ' ' + postal[3:] if rePostalCode.match(postal) else postal

def random_temp_license( prefix = u'TEMP_'):
	numbers = '0123456789'
	numbers_max = len(numbers)-1
	return u''.join( [prefix, ''.join(numbers[random.randint(0,numbers_max)] for i in xrange(15))] )

class LicenseHolder(models.Model):
	last_name = models.CharField( max_length=64, verbose_name=_('Last Name'), db_index=True )
	first_name = models.CharField( max_length=64, verbose_name=_('First Name'), db_index=True )
	
	GENDER_CHOICES=(
		(0, _('Men')),
		(1, _('Women')),
	)
	gender = models.PositiveSmallIntegerField( choices=GENDER_CHOICES, default=0 )
	
	MinAge = 3
	MaxAge = 100
	date_of_birth = models.DateField()
	
	city = models.CharField( max_length=64, blank=True, default='', verbose_name=_('City') )
	state_prov = models.CharField( max_length=64, blank=True, default='', verbose_name=_('State/Prov') )
	nationality = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Nationality') )
	zip_postal = models.CharField( max_length=12, blank=True, default='', verbose_name=_('Zip/Postal') )
	
	email = models.EmailField( blank=True )
	phone = models.CharField( max_length=26, blank=True, default='', verbose_name=_('Phone') )
	
	uci_code = models.CharField( max_length=11, blank=True, default='', db_index=True, verbose_name=_('UCI Code') )
	
	license_code = models.CharField( max_length=32, null=True, unique=True, verbose_name=_('License Code') )
	
	existing_bib = models.PositiveSmallIntegerField( null=True, blank=True, db_index=True, verbose_name=_('Existing Bib') )
	
	existing_tag = models.CharField( max_length=36, null=True, blank=True, unique=True, verbose_name=_('Existing Tag') )
	existing_tag2 = models.CharField( max_length=36, null=True, blank=True, unique=True, verbose_name=_('Existing Tag2') )
	
	suspended = models.BooleanField( default=False, verbose_name=_('Suspended'), db_index=True )
	active = models.BooleanField( default=True, verbose_name=_('Active'), db_index=True )

	SearchTextLength = 256
	search_text = models.CharField( max_length=SearchTextLength, blank=True, default='', db_index=True )
	
	eligible = models.BooleanField( default=True, verbose_name=_('Eligible to Compete'), db_index=True )
	note = models.TextField( null=True, blank=True, verbose_name=_('LicenseHolder Note') )
	
	emergency_contact_name = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Emergency Contact') )
	emergency_contact_phone = models.CharField( max_length=26, blank=True, default='', verbose_name=_('Emergency Contact Phone') )

	def correct_uci_county_code( self ):
		uci_code_save = self.uci_code
		country_code = self.uci_code[:3].upper()
		if country_code and country_code.isalpha() and country_code != iso_uci_country_codes.get(country_code, country_code):
			country_code = iso_uci_country_codes.get(country_code, country_code)
			
		dob = self.date_of_birth.strftime('%Y%m%d')
		self.uci_code = country_code + dob
		if self.uci_code != uci_code_save:
			self.save()
	
	def save( self, *args, **kwargs ):
		self.uci_code = (self.uci_code or '').strip().upper()
		if len(self.uci_code) == 3:
			self.uci_code += self.date_of_birth.strftime( '%Y%m%d' )
			
		if not self.uci_code and ioc_from_country(self.nationality):
			self.uci_code = '{}{}'.format( ioc_from_country(self.nationality), self.date_of_birth.strftime('%Y%m%d') )
		
		if len(self.uci_code) == 11:
			country_code = self.uci_code[:3]
			if country_code != iso_uci_country_codes.get(country_code, country_code):
				self.uci_code = '{}{}'.format( iso_uci_country_codes.get(country_code, country_code), self.uci_code[3:] )
		
		for f in ['last_name', 'first_name', 'city', 'state_prov', 'nationality', 'uci_code']:
			setattr( self, f, (getattr(self, f) or '').strip() )
		
		if not self.nationality and self.uci_code:
			self.nationality = country_from_ioc( self.uci_code ) or self.nationality
		
		if not self.state_prov and self.license_code and self.license_code[:2] in province_codes:
			self.state_prov = province_codes[self.license_code[:2]]
		
		try:
			self.license_code = self.license_code.strip().lstrip('0')
		except Exception as e:
			pass
		
		for f in ['license_code', 'existing_tag', 'existing_tag2']:
			setattr( self, f, fixNullUpper(getattr(self, f)) )
			
		self.zip_postal = validate_postal_code( self.zip_postal )
		
		# If the license_code is TEMP or empty, make a unique temporary code.
		# This is required by Django.
		if self.license_code == u'TEMP' or not self.license_code:
			self.license_code = random_temp_license()

		self.search_text = self.get_search_text()[:self.SearchTextLength]
		
		super(LicenseHolder, self).save( *args, **kwargs )
		
	@property
	def is_temp_license( self ):
		return self.license_code.startswith(u'TEMP') or self.license_code.startswith(u'_')

	@property
	def license_code_export( self ):
		return u'TEMP' if not self.license_code or self.is_temp_license else self.license_code
	
	@property
	def license_code_trunc( self ):
		return self.license_code if len(self.license_code) <= 11 else u'{}...'.format(self.license_code[:11])
	
	@property
	def uci_country( self ):
		if not self.uci_code:
			return None
		country_code = self.uci_code[:3]
		return country_code if country_code in uci_country_codes_set else None
		
	@property
	def uci_code_error( self ):
		if not self:
			return None
		if not self.uci_code:
			return _(u'missing')
			
		self.uci_code = unicode(self.uci_code).upper().replace(u' ', u'')
		
		if len(self.uci_code) != 11:
			return _(u'invalid length for uci code')

		if self.uci_code[:3] not in uci_country_codes_set:
			return _(u'invalid nation code')
			
		try:
			year = int(self.uci_code[3:7])
		except ValueError:
			return _(u'year is not a number')
		try:
			month = int(self.uci_code[7:9])
		except ValueError:
			return _(u'month is not a number')
		try:
			day = int(self.uci_code[9:])
		except ValueError:
			return _(u'day is not a number')
		
		try:
			d = datetime.date(year, month, day)
		except ValueError as e:
			return unicode(e)
		
		if d != self.date_of_birth:
			return _(u'inconsistent with date of birth')
		
		age = datetime.date.today().year - d.year
		if age < self.MinAge:
			return _(u'date too recent')
		if age > self.MaxAge:
			return _(u'date too early')
		return None

	@property
	def date_of_birth_error( self ):
		if not self or not self.date_of_birth:
			return None
		age = datetime.date.today().year - self.date_of_birth.year
		if age < self.MinAge:
			return _(u'age too young')
		if age > self.MaxAge:
			return _(u'age too old')
		return None

	@property
	def emergency_contact_incomplete( self ):
		return not (self.emergency_contact_name and self.emergency_contact_phone)
	
	@property
	def license_code_error( self ):
		return _(u'temp license') if self.is_temp_license else None
	
	@property
	def has_error( self ):
		return self.uci_code_error or self.license_code_error
		
	def __unicode__( self ):
		return '{}, {} ({}, {}, {}, {})'.format(
			self.last_name.upper(), self.first_name,
			self.date_of_birth.isoformat(), self.get_gender_display(),
			self.uci_code, self.license_code
		)
		
	def full_name( self ):
		return u"{}, {}".format(self.last_name.upper(), self.first_name)
		
	def full_license( self ):
		return u', '.join( f for f in [self.uci_code, self.license_code] if f )
		
	def get_location( self ):
		return u', '.join( f for f in [self.city, get_abbrev(self.state_prov)] if f )
		
	def get_search_text( self ):
		return utils.get_search_text( [
				self.last_name, self.first_name,
				self.license_code, self.uci_code,
				self.nationality, self.state_prov, self.city,
				self.existing_tag, self.existing_tag2
			]
		)
		
	def get_unique_tag( self ):
		system_info = SystemInfo.get_singleton()
		if system_info.tag_from_license and self.license_code:
			return getTagFromLicense( self.license_code, system_info.tag_from_license_id )
		else:
			return getTagFormatStr( system_info.tag_template ).format( n=self.id )
	
	def get_existing_tag_str( self ):
		return u', '.join( [t for t in [self.existing_tag, self.existing_tag2] if t] )
	
	def get_participation_as_competitor( self ):
		return Participant.objects.select_related('competition', 'team', 'category').filter(
			license_holder=self, role=Participant.Competitor, category__isnull=False
		).order_by( '-competition__start_date' )
	
	def get_tt_metric( self, ref_date ):
		years = (ref_date - self.date_of_birth).days / 365.26
		dy = years - 24.0	# Fastest estimated year.
		if dy < 0:
			dy *= 4
		return -(dy ** 2)
	
	@classmethod
	def get_duplicates( cls ):
		duplicates = defaultdict( list )
		for last_name, first_name, gender, date_of_birth, pk in LicenseHolder.objects.values_list('last_name','first_name','gender','date_of_birth','pk'):
			key = (
				u'{}, {}'.format(utils.removeDiacritic(last_name).upper(), utils.removeDiacritic(first_name[:1]).upper()),
				gender,
				date_of_birth
			)
			duplicates[key].append( pk )
		
		duplicates = [{
				'key': key,
				'duplicateIds': u','.join(unicode(pk) for pk in pks),
				'license_holders': LicenseHolder.objects.filter(pk__in=pks).order_by( 'search_text' ),
				'license_holders_len': len(pks),
			} for key, pks in duplicates.iteritems() if len(pks) > 1]
			
		duplicates.sort( key=lambda r: r['key'] )
		return duplicates

	@classmethod
	def get_errors( cls ):
		license_holders = sorted(
			set(p.license_holder for p in Participant.objects.all().select_related('license_holder')),
			key=lambda x:x.search_text
		)
		return (lh for lh in license_holders if lh.has_error)
	
	def get_uci_html( self ):
		country = self.uci_country
		return mark_safe('<img src="{}/{}.png"/>&nbsp;{}'.format(static('flags'), country, self.uci_code) ) if country else self.uci_code
	
	class Meta:
		verbose_name = _('LicenseHolder')
		verbose_name_plural = _('LicenseHolders')
		ordering = ['search_text']

#---------------------------------------------------------------
class Waiver(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index=True )
	legal_entity = models.ForeignKey( 'LegalEntity', db_index=True )
	date_signed = models.DateField( null=True, default=None, db_index=True, verbose_name=_('Waiver Signed on') )
	
	class Meta:
		unique_together = (
			('license_holder', 'legal_entity'),
		)
		verbose_name = _('Waiver')
		verbose_name_plural = _('Waivers')

#---------------------------------------------------------------

class TeamHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	discipline = models.ForeignKey( 'Discipline', db_index = True )
	team = models.ForeignKey( 'Team', db_index = True )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def unicode( self ):
		return unicode(self.license_holder) + ' ' + unicode(self.discipline) + ' ' + unicode(self.team) + ' ' + unicode(self.effective_date)
	
	class Meta:
		verbose_name = _('TeamHint')
		verbose_name_plural = _('TeamHints')
		
class CategoryHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	discipline = models.ForeignKey( 'Discipline', db_index = True )
	category = models.ForeignKey( 'Category', db_index = True )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def unicode( self ):
		return unicode(self.license_holder) + ' ' + unicode(self.discipline) + ' ' + unicode(self.category) + ' ' + unicode(self.effective_date)
	
	class Meta:
		verbose_name = _('CategoryHint')
		verbose_name_plural = _('CategoryHints')

class NumberSetEntry(models.Model):
	number_set = models.ForeignKey( 'NumberSet', db_index = True )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	bib = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Bib') )
	
	# If date_lost will only have a value if the number is not lost.
	date_lost = models.DateField( db_index=True, null=True, default=None, verbose_name=_('Date Lost') )
	
	class Meta:
		unique_together = (
			('number_set', 'bib'),
		)

		verbose_name = _('NumberSetEntry')
		verbose_name_plural = _('NumberSetEntries')
		
class FormatTimeDelta( datetime.timedelta ):
	def __repr__( self ):
		fraction, seconds = math.modf( self.total_seconds() )
		seconds = int(seconds)
		return '%d:%02d:%02.3f' % (seconds // (60*60), (seconds // 60) % 60, seconds % 60 + fraction)
	
	def __unicode( self ):
		return unicode( self.__repr__() )
		
class Participant(models.Model):
	competition = models.ForeignKey( 'Competition', db_index=True )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index=True )
	team = models.ForeignKey( 'Team', null=True, db_index=True, on_delete=models.SET_NULL  )
	
	ROLE_NAMES = ( '',	# No zero code.
		_('Team'), _('Official'), _('Organizer'), _('Press'),
	)
	Competitor = 110
	COMPETITION_ROLE_CHOICES = (
		(_('Team'), (
			(Competitor, _('Competitor')),
			(120, _('Manager')),
			(130, _('Coach')),
			(140, _('Doctor')),
			(150, _('Paramedical Asst.')),
			(160, _('Mechanic')),
			(170, _('Driver')),
			(199, _('Staff')),
			)
		),
		(_('Official'), (
			(210, _('Commissaire')),
			(220, _('Timer')),
			(230, _('Announcer')),
			(240, _('Radio Operator')),
			(250, _('Para Classifier')),
			(299, _('Official Staff')),
			)
		),
		(_('Organizer'), (
			(310, _('Administrator')),
			(320, _('Organizer Mechanic')),
			(330, _('Organizer Driver')),
			(399, _('Organizer Staff')),
			)
		),
		(_('Press'), (
			(410, _('Photographer')),
			(420, _('Reporter')),
			)
		),
	)
	role=models.PositiveSmallIntegerField( choices=COMPETITION_ROLE_CHOICES, default=110, verbose_name=_('Role') )
	
	preregistered=models.BooleanField( default=False, verbose_name=_('Preregistered') )
	
	registration_timestamp=models.DateTimeField( auto_now_add=True )
	category=models.ForeignKey( 'Category', null=True, blank=True, db_index=True )
	
	bib=models.PositiveSmallIntegerField( null=True, blank=True, db_index=True, verbose_name=_('Bib') )
	
	tag=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag') )
	tag2=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag2') )

	signature=models.TextField( blank=True, default='', verbose_name=_('Signature') )
	
	@property
	def is_jsignature( self ):
		return self.signature and self.signature.startswith('image/svg+xml;base64')

	paid=models.BooleanField( default=False, verbose_name=_('Paid') )
	confirmed=models.BooleanField( default=False, verbose_name=_('Confirmed') )
	
	note=models.TextField( blank=True, default='', verbose_name=_('Note') )
	
	est_kmh=models.FloatField( default=0.0, verbose_name=_('Est Kmh') )
	seed_early=models.BooleanField( default=False, verbose_name=_('Seed Early') )
	SEED_OPTION_CHOICES = ((1,_('-')),(0,_('Seed Early')),(2,_('Seed Late')),)
	seed_option=models.SmallIntegerField( choices=SEED_OPTION_CHOICES, default=1, verbose_name=_('Seed Option') )
	
	@property
	def est_speed_display( self ):
		return u'{:g} {}{}'.format(
			self.competition.to_local_speed(self.est_kmh),
			self.competition.speed_unit_display,
			u' ({})'.format( self.get_seed_option_display() ) if self.seed_option != 1 else u'',
		)
	
	def get_short_role_display( self ):
		role = self.get_role_display()
	
	@property
	def adjusted_est_kmh( self ):
		return [-1000000.0, 0.0, 1000000][self.seed_option] + self.est_kmh
	
	def save( self, *args, **kwargs ):
		license_holder_update = kwargs.pop('license_holder_update', True)
		number_set_update = kwargs.pop('number_set_update', True)
		
		try:
			self.bib = int(self.bib)
		except (TypeError, ValueError):
			self.bib = None
		if not self.bib or self.bib < 0:
			self.bib = None
		
		competition = self.competition
		license_holder = self.license_holder
		
		for f in ['signature', 'note']:
			setattr( self, f, (getattr(self, f) or '').strip() )
		
		for f in ['tag', 'tag2']:
			setattr( self, f, fixNullUpper(getattr(self, f)) )
		
		if self.role == self.Competitor:
			
			if number_set_update and competition.number_set:
				if self.bib and self.category:
					competition.number_set.assign_bib( license_holder, self.bib )
				
			if license_holder_update:
				if competition.use_existing_tags:
					if license_holder.existing_tag != self.tag or license_holder.existing_tag2 != self.tag2:
						license_holder.existing_tag = self.tag
						license_holder.existing_tag2 = self.tag2
						license_holder.save()
		else:
			self.bib = None
			self.category = None
			self.signature = ''
			self.tag = ''
			self.tag2 = ''
				
		self.propagate_bib_tag()
		return super(Participant, self).save( *args, **kwargs )
	
	@property
	def roleCode( self ):
		return self.role // 100
		
	@property
	def is_with_team( self ):
		return 100 <= self.role <= 199
		
	@property
	def is_with_officials( self ):
		return 100 <= self.role <= 199
		
	@property
	def is_with_organizer( self ):
		return 100 <= self.role <= 199
		
	@property
	def is_competitor( self ):
		return self.role == Participant.Competitor
		
	@property
	def is_seasons_pass_holder( self ):
		return self.competition.seasons_pass and SeasonsPassHolder.objects.filter(seasons_pass=self.competition.seasons_pass, license_holder=self.license_holder).exists()

	@property
	def role_full_name( self ):
		return u'{} {}'.format( self.ROLE_NAMES[self.roleCode], get_role_display() )
	
	@property
	def needs_bib( self ):
		return self.is_competitor and not self.bib
	
	@property
	def needs_tag( self ):
		return self.is_competitor and self.competition.using_tags and not self.tag and not self.tag2
	
	@property
	def name( self ):
		fields = [ getattr(self.license_holder, a) for a in ['first_name', 'last_name', 'uci_code', 'license_code'] ]
		if self.team:
			fields.append( self.team.short_name() )
		return u''.join( [u'{} '.format(self.bib) if self.bib else u'', u', '.join( [f for f in fields if f] )] )
	
	@property
	def full_name_team( self ):
		full_name = self.license_holder.full_name()
		if self.team:
			full_name = u'{}:  {}'.format( full_name, self.team.name )
		return full_name
	
	@property
	def non_existant_waiver( self ):
		legal_entity = self.competition.legal_entity
		if not legal_entity or legal_entity.waiver_expiry_date == datetime.date(1970,1,1):
			return False
		return not Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).first()
	
	@property
	def expired_waiver( self ):
		legal_entity = self.competition.legal_entity
		if not legal_entity or legal_entity.waiver_expiry_date == datetime.date(1970,1,1):
			return False
		waiver = Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).first()
		return waiver and waiver.date_signed < legal_entity.waiver_expiry_date
	
	@property
	def has_unsigned_waiver( self ):
		legal_entity = self.competition.legal_entity
		if not legal_entity or legal_entity.waiver_expiry_date == datetime.date(1970,1,1):
			return False
		waiver = Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).first()
		return not waiver or waiver.date_signed < legal_entity.waiver_expiry_date
	
	def sign_waiver_now( self ):
		legal_entity = self.competition.legal_entity
		if legal_entity:
			waiver = Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).first()
			if waiver:
				waiver.date_signed = datetime.date.today()
				waiver.save()
			else:
				Waiver(
					license_holder=self.license_holder,
					legal_entity=legal_entity,
					date_signed=datetime.date.today()
				).save()
	
	def unsign_waiver_now( self ):
		legal_entity = self.competition.legal_entity
		if legal_entity:
			Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).delete()
	
	def __unicode__( self ):
		return self.name
	
	def add_to_default_optional_events( self ):
		ParticipantOption.set_option_ids(
			self,
			set( event.option_id for event in self.competition.get_events() if event.select_by_default and event.could_participate(self) )
				if self.category else []
		)
	
	def init_default_values( self ):
		if self.competition.use_existing_tags:
			self.tag  = self.license_holder.existing_tag
			self.tag2 = self.license_holder.existing_tag2
	
		def init_values( pp ):
			if not self.est_kmh and pp.competition.discipline==self.competition.discipline and pp.est_kmh:
				self.est_kmh = pp.est_kmh
			
			if not self.team and pp.team:
				team = pp.team
				while 1:
					try:
						team = team.is_now_team
					except ObjectDoesNotExist:
						break
				self.team = team
			if not self.role:
				self.role = pp.role
			if not self.category and pp.competition.category_format == self.competition.category_format:
				self.category = pp.category
			return self.team and self.role and self.category
	
		self.role = 0
		init_date = None
		
		for pp in Participant.objects.filter(
				role=Participant.Competitor,
				license_holder=self.license_holder).exclude(category__isnull=True).order_by('-competition__start_date', 'category__sequence')[:8]:
			if init_values(pp):
				init_date = pp.competition.start_date
				break

		# After we found a default category, try to get the bib number.
		if not self.bib and self.competition.number_set:
			self.bib = self.competition.number_set.get_bib( self.competition, self.license_holder, self.category )
		
		# If we still don't have an est_kmh, try to get one from a previous competition of the same discipline.
		if not self.est_kmh:
			for est_kmh in Participant.objects.filter(
						license_holder=self.license_holder,
						role=Participant.Competitor,
						competition__discipline=self.competition.discipline,
					).exclude(
						est_kmh=0.0
					).order_by(
						'-competition__start_date'
					).values_list('est_kmh', flat=True):
				self.est_kmh = est_kmh
				break
		
		try:
			th = TeamHint.objects.get( license_holder=self.license_holder, discipline=self.competition.discipline )
			if init_date is None or th.effective_date > init_date:
				init_date = th.effective_date
				self.team = th.team
		except TeamHint.DoesNotExist:
			pass
		
		if self.is_seasons_pass_holder:
			self.paid = True
		
		if not self.role:
			self.role = Participant._meta.get_field_by_name('role')[0].default
		
		if self.role != self.Competitor:
			self.bib = None
			self.category = None
			if self.role >= 200:			# Remove team for non-team roles.
				self.team = None
		
		return self
	
	def good_uci_code( self ):		return self.license_holder.uci_code_error is None
	def good_license( self ):		return not self.license_holder.is_temp_license
	def good_emergency_contact( self ):	return not self.license_holder.emergency_contact_incomplete
	
	def good_bib( self ):			return self.is_competitor and self.bib
	def good_category( self ):		return self.is_competitor and self.category
	def good_tag( self ):			return not self.needs_tag
	def good_team( self ):			return self.is_competitor and self.team
	def good_paid( self ):			return self.is_competitor and self.paid
	def good_signature( self ):		return self.signature or (not self.competition.show_signature)
	def good_est_kmh( self ):		return self.est_kmh or (not self.has_tt_events())
	def good_waiver( self ):		return not self.has_unsigned_waiver
	def good_eligible( self ):		return not self.is_competitor or self.license_holder.eligible
	
	def can_start( self ):
		return (
			self.good_eligible() and
			self.good_bib() and
			self.good_category() and
			self.good_tag() and
			self.good_waiver() and
			self.good_paid() and
			self.good_signature()
		)
	
	def can_tt_start( self ):
		return (
			self.good_eligible() and
			self.good_category()
		)
	
	@property
	def show_confirm( self ):
		return (
			self.is_competitor and
			self.can_start()
		)
	
	@property
	def is_done( self ):
		if self.is_competitor:
			return (
				self.can_start() and
				self.show_confirm and
				self.good_uci_code() and
				self.good_license() and
				self.good_emergency_contact() and
				self.good_est_kmh()
			)
		elif self.role < 200:
			return (
				self.team and
				self.good_uci_code()
			)
		else:
			return self.good_uci_code()
	
	def auto_confirm( self ):
		if self.competition.start_date <= datetime.date.today() <= self.competition.finish_date and self.show_confirm:
			self.confirmed = True
		return self
	
	def propagate_bib_tag( self ):
		category_numbers = CategoryNumbers.objects.filter( competition=self.competition, categories=self.category ).first()
		if not category_numbers:
			return
		Participant.objects.filter(
			competition=self.competition,
			license_holder=self.license_holder,
			role=Participant.Competitor,
			category__in=category_numbers.categories.all()
		).exclude(
			id=self.id
		).update(
			bib=self.bib,
			tag=self.tag,
			tag2=self.tag2
		)
		
	def update_bib_new_category( self ):
		if self.competition.number_set:
			self.bib = self.competition.number_set.get_bib( self.competition, self.license_holder, self.category )
			return
		
		category_numbers = CategoryNumbers.objects.filter( competition=self.competition, categories=self.category ).first()
		if not category_numbers:
			self.bib = None
			return
		
		compatible_participant = Participant.objects.filter(
			competition=self.competition,
			license_holder=self.license_holder,
			role=Participant.Competitor,
			category__in=category_numbers.categories.all()
		).exclude(
			id=self.id
		).first()
		
		self.bib = compatible_participant.bib if compatible_participant else None
	
	def get_other_category_participants( self ):
		return list(
			Participant.objects.filter(
				competition=self.competition,
				license_holder=self.license_holder,
				role=self.Competitor,
			).exclude( id=self.id )
		)
	
	def get_category_participants( self ):
		return list(
			Participant.objects.filter(
				competition=self.competition,
				license_holder=self.license_holder,
				role=self.Competitor,
			)
		)
	
	def get_bib_conflicts( self ):
		if not self.bib:
			return []
		conflicts = Participant.objects.filter( competition=self.competition, role=Participant.Competitor, bib=self.bib )
		category_numbers = self.competition.get_category_numbers( self.category ) if self.category else None
		if category_numbers:
			conflicts = conflicts.filter( category__in=category_numbers.categories.all() )
		conflicts.exclude( pk=self.pk )
		return list(conflicts)
	
	def get_start_waves( self ):
		if not self.category:
			return []
		waves = sorted( Wave.objects.filter(event__competition=self.competition, categories=self.category), key=Wave.get_start_time )
		waves = [w for w in waves if w.is_participating(self)]
		reg_closure_minutes = SystemInfo.get_reg_closure_minutes()
		for w in waves:
			w.is_late = w.reg_is_late( reg_closure_minutes, self.registration_timestamp )
		return waves
	
	def get_start_wave_tts( self ):
		if not self.category:
			return []
		waves = sorted( WaveTT.objects.filter(event__competition=self.competition, categories=self.category), key=lambda w: w.sequence )
		waves = [w for w in waves if w.is_participating(self)]
		reg_closure_minutes = SystemInfo.get_reg_closure_minutes()
		for w in waves:
			w.is_late = w.reg_is_late( reg_closure_minutes, self.registration_timestamp )
		return waves
	
	def get_participant_events( self ):
		return self.competition.get_participant_events(self)
		
	def has_optional_events( self ):
		return any( optional for event, optional, entered in self.get_participant_events() )
	
	def has_tt_events( self ):
		return any( entered and event.event_type == 1 for event, optional, entered in self.get_participant_events() )
	
	def has_any_events( self ):
		return self.competition.has_any_events(self)
	
	def event_count( self ):
		return sum( 1 for event, optional, entered in self.get_participant_events() if entered )

	def event_mass_start_count( self ):
		return sum( 1 for event, optional, entered in self.get_participant_events() if event.event_type == 0 and entered )
	
	def event_tt_count( self ):
		return sum( 1 for event, optional, entered in self.get_participant_events() if event.event_type == 1 and entered )
	
	@property
	def allocated_bibs( self ):
		return self.competition.number_set.numbersetentry_set.filter( license_holder=self.license_holder, date_lost=None ).order_by('bib').values_list('bib', flat=True) \
			if self.competition.number_set else []
	
	def explain_integrity_error( self ):
		participant = Participant.objects.filter(competition=self.competition, category=self.category, license_holder=self.license_holder).first()
		if participant:
			return True, _('This LicenseHolder is already in this Category'), participant
			
		participant = Participant.objects.filter(competition=self.competition, category=self.category, license_holder=self.license_holder).first()
		if participant:
			return True, _('This LicenseHolder is already in this Category'), participant
			
		participant = Participant.objects.filter(competition=self.competition, category=self.category, bib=self.bib).first()
		if participant:
			return True, _('A Participant is already in this Category with the same Bib.  Assign "No Bib" first, then try again.'), participant
		
		if self.tag:
			participant = Participant.objects.filter(competition=self.competition, category=self.category, tag=self.tag).first()
			if participant:
				return True, _('A Participant is already in this Category with the same Chip Tag.  Assign empty "Tag" first, and try again.'), participant
			
		if self.tag2:
			participant = Participant.objects.get(competition=self.competition, category=self.category, tag2=self.tag2).first()
			if participant:
				return True, _('A Participant is already in this Category with the same Chip Tag2.  Assign empty "Tag2" first, and try again.'), participant
		
		return False, _('Unknown Integrity Error.'), None
	
	def get_tag_str( self ):
		return u', '.join( [t for t in [self.tag, self.tag2] if t] )
	
	class Meta:
		unique_together = (
			('competition', 'category', 'license_holder'),
			('competition', 'category', 'bib'),
			('competition', 'category', 'tag'),
			('competition', 'category', 'tag2'),
		)
		ordering = ['license_holder__search_text']
		verbose_name = _('Participant')
		verbose_name_plural = _('Participants')

#---------------------------------------------------------------------------------------------------------

class EntryTT( models.Model ):
	event = models.ForeignKey( 'EventTT', db_index = True, verbose_name=_('Event') )
	participant = models.ForeignKey( 'Participant', db_index = True, verbose_name=_('Participant') )
	
	est_speed = models.FloatField( default=0.0, verbose_name=_('Est. Speed') )
	hint_sequence = models.PositiveIntegerField( default=0, verbose_name = _('Hint Sequence') )
	
	start_sequence = models.PositiveIntegerField( default = 0, db_index = True, verbose_name = _('Start Sequence') )
	
	start_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Start Time') )
	
	finish_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Finish Time') )
	adjustment_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Adjustment Time') )
	adjustment_note = models.CharField( max_length = 128, default = '', verbose_name=_('Adjustment Note') )
	
	@transaction.atomic
	def move_to( self, start_sequence_target ):
		if self.start_sequence == start_sequence_target:
			return
		while self.start_sequence != start_sequence_target:
			dir = -1 if self.start_sequence > start_sequence_target else 1
			try:
				e = EntryTT.objects.get(event=self.event, start_sequence=self.start_sequence+dir)
				self.start_sequence, e.start_sequence = e.start_sequence, self.start_sequence
				self.start_time, e.start_time = e.start_time, self.start_time
				e.save()
			except (EntryTT.DoesNotExist, EntryTT.MultipleObjectsReturned) as e:
				self.save()
				return False
		self.save()
		return True
	
	class Meta:
		unique_together = (
			('event', 'participant',),
		)
		index_together = (
			('event', 'start_sequence',),
		)

		verbose_name = _("Time Trial Entry")
		verbose_name_plural = _("Time Trial Entry")
		ordering = ['start_time']

class EventTT( Event ):
	def __init__( self, *args, **kwargs ):
		kwargs['event_type'] = 1
		super( EventTT, self ).__init__( *args, **kwargs )
		
	create_seeded_startlist = models.BooleanField( default=True, verbose_name=_('Create Seeded Startlist'),
		help_text=_('If True, seeded start times will be generated in the startlist for CrossMgr.  If False, no seeded times will be generated, and the TT time will start on the first recorded time in CrossMgr.') )

	def create_initial_seeding( self ):
		while EntryTT.objects.filter(event=self).exists():
			with transaction.atomic():
				ids = EntryTT.objects.filter(event=self).values_list('pk', flat=True)[:999]
				EntryTT.objects.filter(pk__in=ids).delete()
		
		min_gap = datetime.timedelta( seconds=10 )
		zero_gap = datetime.timedelta( seconds=0 )
		
		empty_gap_before_wave = zero_gap
		
		sequenceCur = 1
		tCur = datetime.timedelta( seconds = 0 )
		for wave_tt in self.wavett_set.all():
			participants = sorted( [p for p in wave_tt.get_participants_unsorted() if p.can_tt_start()], key=wave_tt.get_sequence_key() )
			
			# Carry the "before gaps" of empty waves.
			if not participants:
				empty_gap_before_wave = max( empty_gap_before_wave, wave_tt.gap_before_wave )
				continue
			
			last_fastest = len(participants) - wave_tt.num_fastest_participants
			entry_tt_pending = []
			for i, p in enumerate(participants):
				rider_gap = max(
					wave_tt.fastest_participants_start_gap if i >= last_fastest else zero_gap,
					wave_tt.regular_start_gap,
					min_gap,
				)
				tCur += max( max(empty_gap_before_wave, wave_tt.gap_before_wave) if i == 0 else zero_gap, rider_gap )
				
				entry_tt_pending.append( EntryTT(event=self, participant=p, start_time=tCur, start_sequence=sequenceCur) )
				sequenceCur += 1
				
			EntryTT.objects.bulk_create( entry_tt_pending )
			entry_tt_pending = []
			empty_gap_before_wave = zero_gap
	
	def get_start_time( self, participant ):
		try:
			return EntryTT.objects.get(event=self, participant=participant).start_time
		except EntryTT.DoesNotExist as e:
			return None
			
	def get_participants_seeded( self ):
		participants = set()
		for w in self.get_wave_set().all():
			participants_cur = set( w.get_participants_unsorted().select_related('competition','license_holder','team') )
			for p in participants_cur:
				p.wave = w
			participants |= participants_cur

		participants = list( participants )
		
		if self.create_seeded_startlist:
			start_times = {
				pk: datetime.timedelta(seconds=start_time.total_seconds())
				for pk, start_time in EntryTT.objects.filter(
						participant__competition=self.competition,
						event=self,
					).values_list(
						'participant__pk',
						'start_time',
					)
			}
		else:
			start_times = {}
			
		for p in participants:
			p.start_time = start_times.get( p.pk, None )
			p.clock_time = None if p.start_time is None else self.date_time + p.start_time
		
		participants.sort(
			key=lambda p: (
				p.start_time.total_seconds() if p.start_time else 1000.0*24.0*60.0*60.0,
				p.bib or 0, p.license_holder.date_of_birth,
			)
		)
		
		tDelta = datetime.timedelta( seconds = 0 )
		for i, p in enumerate(participants):
			p.gap_change = 0
			if i > 0:
				try:
					tDeltaCur = p.start_time - participants[i-1].start_time
					if tDeltaCur != tDelta:
						if i > 1:
							p.gap_change = 1 if tDeltaCur > tDelta else -1
						tDelta = tDeltaCur
				except Exception as e:
					pass
		
		return participants
	
	def repair_seeding( self ):
		if not EntryTT.objects.filter(event=self).exists():
			self.create_initial_seeding()
		
		participants = self.get_participants_seeded()
		start_time_deltas = []
		p_last = None
		for p in participants:
			if p.start_time:
				if p_last:
					start_time_deltas.append( p.start_time.total_seconds() - p_last.start_time.total_seconds() )
				p_last = p
		
		start_time_deltas.sort()
		try:
			gap_median = datetime.timedelta( seconds=start_time_deltas[len(start_time_deltas)//2] )
		except IndexError:
			gap_median = datetime.timedelta( seconds=60 )
		
		entry_tt_pending = []
		tCur = datetime.timedelta( seconds=0 )
		for sequenceCur, p in enumerate(participants, 1):
			if p.start_time:
				tCur = p.start_time
			else:
				p.start_time = tCur + gap_median
				tCur = p.start_time
				entry_tt_pending.append( EntryTT(event=self, participant=p, start_time=tCur, start_sequence=sequenceCur) )
				
		EntryTT.objects.bulk_create( entry_tt_pending )

	def get_unseeded_count( self ):
		return sum( 1 for p in self.get_participants_seeded() if p.start_time is None ) if self.create_seeded_startlist else 0
	
	def get_bad_start_count( self ):
		return sum( wave_tt.get_bad_start_count() for wave_tt in self.wavett_set.all() )
	
	def has_unseeded( self ):
		if not self.create_seeded_startlist:
			return False
		participants = set( p.pk for p in self.get_participants() )
		start_times = set(
			EntryTT.objects.filter(
				participant__competition=self.competition,
				event=self,
			).values_list(
				'participant__pk',
				flat=True,
			)
		)
		participants_with_start_times = participants & start_times
		return len(participants_with_start_times) < len(participants)

	# Time Trial fields
	class Meta:
		verbose_name = _('Time Trial Event')
		verbose_name_plural = _('Time Trial Events')

#---------------------------------------------------------------------------------------------

class WaveTT( WaveBase ):
	event = models.ForeignKey( EventTT, db_index = True )
	
	sequence = models.PositiveSmallIntegerField( default=0, verbose_name = _('Sequence') )
	
	# Fields for assigning start times.	
	gap_before_wave = DurationField.DurationField( verbose_name=_('Gap Before Wave'), default = 5*60 )
	regular_start_gap = DurationField.DurationField( verbose_name=_('Regular Start Gap'), default = 1*60 )
	fastest_participants_start_gap = DurationField.DurationField( verbose_name=_('Fastest Participants Start Gap'), default = 2*60 )
	num_fastest_participants = models.PositiveSmallIntegerField(
						verbose_name=_('Number of Fastest Participants'),
						choices=[(i, '%d' % i) for i in xrange(0, 16)],
						help_text = 'Participants to get the Fastest gap',
						default = 5)
						
	# Sequence option.
	est_speed_increasing = 0
	age_increasing = 1
	bib_increasing = 2
	age_decreasing = 3
	bib_decreasing = 4
	SEQUENCE_CHOICES = (
		(_("Increasing"), (
				(est_speed_increasing, _("Est. Speed - Increasing")),
				(age_increasing, _("Youngest to Oldest")),
				(bib_increasing, _("Bib - Increasing")),
			),
		),
		(_("Decreasing"), (
				(age_decreasing, _("Oldest to Youngest")),
				(bib_decreasing, _("Bib - Decreasing")),
			),
		),
	)
	sequence_option = models.PositiveSmallIntegerField(
		verbose_name=_('Sequence Option'),
		choices = SEQUENCE_CHOICES,
		help_text = 'Criteria used to order participants in the wave',
		default=0 )
	
	def save( self, *args, **kwargs ):
		init_sequence( WaveTT, self )
		return super( WaveTT, self ).save( *args, **kwargs )
	
	def get_speed( self, participant ):
		try:
			entry_tt = EntryTT.objects.get( event=self.event, participant=participant )
		except Exception as e:
			return None
		try:
			distance = self.distance
			return (distance / (entry_tt.finish_time - entry_tt.start_time).total_seconds()) * (60.0*60.0)
		except Exception as e:
			return None
	
	def get_sequence_key( self ):
		if self.sequence_option == self.est_speed_increasing:
			return lambda p: (
				p.seed_option,
				p.est_kmh,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(datetime.date.today()),
				p.id,
			)
		elif self.sequence_option == self.age_increasing:
			return lambda p: (
				p.seed_option,
				p.license_holder.date_of_birth,
				-(p.bib or 0),
				p.id,
			)
		elif self.sequence_option == self.bib_increasing:
			return lambda p: (
				p.seed_option,
				p.bib or 0,
				p.license_holder.get_tt_metric(datetime.date.today()),
				p.id,
			)
		elif self.sequence_option == self.age_decreasing:
			return lambda p: (
				p.seed_option,
				datetime.date(3000,1,1) - p.license_holder.date_of_birth,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(datetime.date.today()),
				p.id,
			)
		elif self.sequence_option == self.bib_decreasing:
			return lambda p: (
				p.seed_option,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(datetime.date.today()),
				p.id,
			)
	
	@property
	def gap_rules_html( self ):
		summary = [u'<table>']
		try:
			for label, value in (
					(_('GapBefore'), self.gap_before_wave),
					(_('RegularGap'), self.regular_start_gap),
					(_('FastGap'), self.fastest_participants_start_gap if self.num_fastest_participants else None),
					(_('NumFast'), self.num_fastest_participants if self.num_fastest_participants else None),
				):
				if value is not None:
					summary.append( u'<tr><td class="text-right">{}&nbsp&nbsp</td><td class="text-right">{}</td><tr>'.format(label, unicode(value)) )
		except Exception as e:
			return e
		summary.append( '</table>' )
		return u''.join( summary )
	
	@property
	def gap_rules_text( self ):
		summary = []
		try:
			for label, value in (
					(_('GapBefore'), self.gap_before_wave),
					(_('RegularGap'), self.regular_start_gap),
					(_('FastGap'), self.fastest_participants_start_gap if self.num_fastest_participants else None),
					(_('NumFast'), self.num_fastest_participants if self.num_fastest_participants else None),
				):
				if value is not None:
					summary.append( u'{}={}'.format(label, unicode(value)) )
		except Exception as e:
			return e
		return u' '.join( summary )
	
	def get_participants( self ):
		participants = list( self.get_participants_unsorted().select_related('license_holder','team') )
		
		if not self.event.create_seeded_startlist:
			participants.sort( key=lambda p: p.bib or 0 )
			for p in participants:
				p.start_time = None
				p.clock_time = None
			return participants
		
		start_times = {
			pk: start_time
			for pk, start_time in EntryTT.objects.filter(
					participant__competition=self.event.competition,
					event=self.event
				).values_list(
					'participant__pk',
					'start_time',
				)
		}
		for p in participants:
			p.start_time = start_times.get( p.pk, None )
			p.clock_time = None if p.start_time is None else self.event.date_time + p.start_time
		
		participants.sort( key=lambda p: (p.start_time if p.start_time else datetime.timedelta(days=100), p.bib or 0) )
		
		tDelta = datetime.timedelta(seconds = 0)
		for i in xrange(1, len(participants)):
			pPrev = participants[i-1]
			p = participants[i]
			try:
				tDeltaCur = p.start_time - pPrev.start_time
				if tDeltaCur != tDelta:
					if i > 1:
						p.gap_change = True
					tDelta = tDeltaCur
			except Exception as e:
				pass
		
		return participants
	
	def get_unseeded_participants( self ):
		if not self.event.create_seeded_startlist:
			return []
		
		has_start_time = set(
			EntryTT.objects.filter(
				participant__competition=self.event.competition,
				event=self.event
			).values_list(
				'participant__pk',
				flat=True
			)
		)
		return [p for p in self.get_participants_unsorted() if p.pk not in has_start_time]
		
	def get_bad_start_count( self ):
		return sum( 1 for p in self.get_participants_unsorted() if not p.can_start() )
	
	class Meta:
		verbose_name = _('TTWave')
		verbose_name_plural = _('TTWaves')
		ordering = ['sequence']

class ParticipantOption( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True )
	participant = models.ForeignKey( Participant, db_index = True )
	option_id = models.PositiveIntegerField( verbose_name = ('Option Id') )
	
	@staticmethod
	@transaction.atomic
	def set_option_ids( participant, option_ids = [] ):
		ParticipantOption.objects.filter(competition=participant.competition, participant=participant).delete()
		ParticipantOption.objects.bulk_create(
			[ParticipantOption( competition=participant.competition, participant=participant, option_id=option_id )
				for option_id in set(option_ids)]
		)
	
	@staticmethod
	@transaction.atomic
	def sync_option_ids( participant, option_id_included = {} ):
		''' Expected option_id_included to be { option_id: True/False }. '''
		ParticipantOption.objects.filter(
			competition=participant.competition,
			participant=participant,
			option_id__in = option_id_included.keys()
		).delete()
		for option_id, included in option_id_included.iteritems():
			if included:
				ParticipantOption( competition=participant.competition, participant=participant, option_id=option_id ).save()
	
	@staticmethod
	def get_option_ids( competition, participant ):
		return ParticipantOption.objects.filter(competition=competition, participant=participant).values_list('option_id', flat=True)
	
	@staticmethod
	def delete_option_id( competition, option_id ):
		ParticipantOption.objects.filter(competition=competition, option_id=option_id).delete()
	
	@staticmethod
	@transaction.atomic
	def set_event_option_id( competition, event ):
		''' Get a unique option_id across MassStart and Time Trial events for this competition. '''
		ids = set()
		for EventClass in (EventMassStart, EventTT):
			ids |= set( EventClass.objects.filter(competition=competition)
							.exclude(option_id=0)
							.values_list('option_id', flat=True) )
		for id in xrange(1, 1000000):
			if id not in ids:
				break
		event.option_id = id
		event.save()

	class Meta:
		unique_together = (
			('competition', 'participant','option_id'),
		)
		index_together = (
			('competition', 'participant','option_id'),
			('competition', 'participant'),
			('competition', 'option_id'),
		)
		verbose_name = _("Participant Option")
		verbose_name_plural = _("Participant Options")

#-------------------------------------------------------------------------------------

@receiver( pre_delete, sender=EventMassStart )
@receiver( pre_delete, sender=EventTT )
def clean_up_event_option_id( sender, **kwargs ):
	event = kwargs.get('instance', None)
	if event and event.optional:
		ParticipantOption.objects.filter(competition=event.competition, option_id=event.option_id).delete()

#-------------------------------------------------------------------------------------

def license_holder_merge_duplicates( license_holder_merge, duplicates ):
	duplicates = list( set(list(duplicates) + [license_holder_merge]) )
	pks = [lh.pk for lh in duplicates if lh != license_holder_merge]
	if not pks:
		return
		
	# Cache and delete the Participant Options.
	participant_options = [(po.participant.pk, po) for po in ParticipantOption.objects.filter( participant__license_holder__pk__in=[lh.pk for lh in duplicates] ) ]
	for participant_pk, po in participant_options:
		po.delete()
	
	# Cache and delete the Participants.
	participants = list(Participant.objects.filter(license_holder__pk__in=[lh.pk for lh in duplicates]))
	participants.sort( key = lambda p: 0 if p.license_holder == license_holder_merge else 1 )
	for p in participants:
		p.delete()
		
	# Add back Participants that point to the merged license_holder.
	competition_participant = {}
	participant_map = {}
	for p in participants:
		pk_old = p.pk
		p.pk = None
		p.license_holder = license_holder_merge
		if p.explain_integrity_error()[0]:
			continue
		p.save( license_holder_update=False, number_set_update=False )
		competition_participant[p.competition] = p
		participant_map[pk_old] = p
	
	# Add back ParticipantOptions that point to the corresponding new Participant.
	for participant_pk, po in participant_options:
		po.pk = None
		try:
			po.participant = participant_map[participant_pk]
		except KeyError:
			try:
				po.participant = competition_participant[po.competition]
			except KeyError:
				continue
		if ParticipantOption.objects.filter(competition=po.competition, participant=po.participant, option_id=po.option_id).exists():
			continue
		po.save()
	
	# Ensure the merged entry is added to every Season's Passes.
	sph_duplicates = set( SeasonsPassHolder.objects.filter(license_holder__pk__in=pks) )
	sph_merge = set( SeasonsPassHolder.objects.filter(license_holder=license_holder_merge) )
	sph_missing = sph_duplicates.difference( sph_merge )
	for sph in sph_missing:
		sph.pk = None
		sph.license_holder = license_holder_merge
		sph.save()
	
	# Ensure that numbers in the number set are owned by the remaining license_holder.
	for ns in NumberSet.objects.all():
		nse_existing = list( NumberSetEntry.objects.filter(number_set=ns, license_holder__pk__in=pks).values_list('bib', 'date_lost') )
		NumberSetEntry.objects.filter(number_set=ns, license_holder__pk__in=pks).delete()
		for bib, date_lost in nse_existing:
			if not NumberSetEntry.objects.filter( number_set=ns, bib=bib ).exists():
				NumberSetEntry( number_set=ns, bib=bib, license_holder=license_holder_merge, date_lost=date_lost ).save()
	
	# Combine waivers.  Preserve most recent date_signed for all legal entities.
	for w in Waiver.objects.filter( license_holder__pk__in=pks ):
		w_merge = Waiver.objects.filter( license_holder=license_holder_merge, legal_entity=w.legal_entity ).first()
		if not w_merge:								# Add waiver if it doesn't exist.
			Waiver( license_holder=license_holder_merge, legal_entity=w.legal_entity, date_signed=w.date_signed ).save()
		elif w_merge.date_signed < w.date_signed:	# Else update to more recent date signed if necessary.
			w_merge.date_signed = w.date_signed
			w_merge.save()
	
	# Final delete.  Cascade delete will clean up old SeasonsPass and Waiver entries.
	LicenseHolder.objects.filter( pk__in=pks ).delete()

#-----------------------------------------------------------------------------------------------
# Apply upgrades.
#
'''
def bad_data_test():
	fields = dict(
		last_name = '00-TEST-LAST-NAME',
		first_name = '00-TEST-FIRST-NAME',
		date_of_birth = datetime.datetime.today(),
	
		license_code = '0000{}'.format( random.randint(0,10000) ),
	
		existing_tag = '0000{}'.format( random.randint(0,10000) ),
		existing_tag2 = '0000{}'.format( random.randint(0,10000) ),
	)
	
	# Use bulk create to avoid calling the save method (otherwise data validation would take place)
	LicenseHolder.objects.bulk_create([
		LicenseHolder( **fields ),
	] )
	print list(LicenseHolder.objects.filter(last_name='00-TEST-LAST-NAME'))
'''

def fix_bad_license_codes():
	q = Q(license_code__startswith='0') or Q(existing_tag__startswith='0') or Q(existing_tag2__startswith='0')
	success = True
	while success:
		success = False
		with transaction.atomic():
			for lh in LicenseHolder.objects.filter(q)[:999]:
				lh.save()		# performs field validation.
				success = True
	
	q = Q(tag__startswith='0') or Q(tag2__startswith='0')
	success = True
	while success:
		success = False
		with transaction.atomic():
			for p in Participant.objects.filter(q)[:999]:
				p.save()		# performs field validation.
				success = True

def fix_non_unique_number_set_entries():
	for ns in NumberSet.objects.all():
		ns.normalize()

def models_fix_data():
	print 'Removing leading zeroes in license codes and chip tags...'
	fix_bad_license_codes()
	fix_non_unique_number_set_entries()



