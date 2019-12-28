from . import patch_sqlite_text_factory	# Must be first.

import re
import os
import math
from heapq import heappush
import datetime
import base64
import operator
import random
import itertools
from collections import defaultdict
try:
	from StringIO import StringIO
	BytesIO = StringIO
except:
	from io import StringIO, BytesIO
import locale

from django.db import models, connection
from django.db import transaction, IntegrityError
from django.db.models import Q, F, Max, Count

from django.contrib.contenttypes.models import ContentType

from django.utils import timezone
from django.utils.timezone import get_default_timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy

from django.core.exceptions import ObjectDoesNotExist
from django.templatetags.static import static
from django.utils.html import escape

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from . import DurationField
from .get_abbrev import get_abbrev

from .get_id import get_id

from . import utils
from .utils import safe_print
from .TagFormat import getValidTagFormatStr, getTagFormatStr, getTagFromLicense, getLicenseFromTag
from .CountryIOC import uci_country_codes_set, ioc_from_country, iso_uci_country_codes, country_from_ioc, province_codes, ioc_from_code
from .large_delete_all import large_delete_all
from .WriteLog import writeLog

def get_ids( q, fname=None ):
	if fname:
		if not fname.endswith( '__id' ):
			fname += '__id'
	else:
		fname = 'id'
	return q.values_list( fname, flat=True )

def duration_field_0():  return 0
def duration_field_1m(): return 60
def duration_field_2m(): return 2*60
def duration_field_3m(): return 3*60
def duration_field_4m(): return 4*60
def duration_field_5m(): return 5*60

invalid_date_of_birth = datetime.date(1900,1,1)

class BulkSave( object ):
	def __init__( self ):
		self.objects = []
		
	def flush( self ):
		if self.objects:
			with transaction.atomic():
				for o in self.objects:
					o.save()		# Also performs field validation.
			del self.objects[:]
				
	def append( self, obj ):
		self.objects.append( obj )
		if len(self.objects) >= 998:
			self.flush()

	def __enter__( self ):
		return self

	def __exit__( self, type, value, traceback ):
		self.flush()

def ordinal( n ):
	return "{}{}".format(n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

def fixNullUpper( s ):
	if not s:
		return None
	s = (s or u'').strip()
	if s:
		return utils.removeDiacritic(s).upper().lstrip('0')
	else:
		return None

def getSrcStr( fname ):
	ftype = os.path.splitext(fname)[1][1:].lower()
	if ftype == 'jpeg':
		ftype = 'jpg'
	with open(fname, 'rb') as f:
		return 'data:image/{};base64,{}'.format(ftype, base64.encodestring(f.read()))

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
def validate_sequence( elements ):
	with transaction.atomic():
		for seq, e in enumerate(list(elements)):
			if e.sequence != seq:
				e.sequence = seq
				e.save()
	
class Sequence( models.Model ):
	sequence = models.PositiveSmallIntegerField( default=32767, blank=True, verbose_name=_('Sequence') )

	def get_container( self ):
		assert False, 'Please implement function get_container().'

	def validate_sequence( self ):
		validate_sequence( self.get_container().order_by('sequence') )
				
	def prev( self ):
		return self.get_container().filter( sequence=self.sequence-1 ).first()
	
	def next( self ):
		return self.get_container().filter( sequence=self.sequence+1 ).first()
	
	def first( self ):
		return self.get_container().order_by('sequence').first()
		
	def last( self ):
		return self.get_container().order_by('sequence').last()

	def move_to( self, i ):
		elements = list( self.get_container().all() )
		i = max( 0, min( i, len(elements) ) )
		elements.remove( self )
		elements.insert( i, self )
		self.sequence = -1
		validate_sequence( elements )
		
	def move_lower( self ):
		self.move_to( self.sequence-1 )

	def move_higher( self ):
		self.move_to( self.sequence+1 )

	def move_to_head( self ):
		self.move_to( 0 )

	def move_to_tail( self ):
		self.move_to( 32767 )
		
	def move( self, move_direction ):
		if move_direction == 0:
			self.move_to( 0 )
		elif move_direction == 1:
			self.move_higher()
		elif move_direction == -1:
			self.move_lower()
		else:
			self.move_to_tail()

	def get_sequence_max( self ):
		return self.get_container().count()
	
	class Meta:
		ordering = ['sequence']
		abstract = True

#----------------------------------------------------------------------------------------
class SystemInfo(models.Model):
	tcUniversallyUnique, tcDatabaseID, tcLicenseCode = tuple(range(3))
	TAG_CREATION_CHOICES = (
		(tcUniversallyUnique,	_('Universally Unique')),
		(tcDatabaseID,			_('From Database ID')),
		(tcLicenseCode,			_('From License Code')),
	)
	tag_creation = models.PositiveSmallIntegerField( default=0, choices=TAG_CREATION_CHOICES,
		verbose_name=_('Tag Creation'),
		help_text=_("Specify how to create RFID tags.")
	)
	
	tag_bits = models.PositiveSmallIntegerField( default=96, choices=[(i,'{}'.format(i)) for i in (64,96)],
		verbose_name=_('EPC Bits per Tag'),
		help_text=_("EPC Bits available if generating Universally Unique tags.") )

	tag_template = models.CharField( max_length = 24, verbose_name = _('Tag Template'),
		help_text=_("Template if generating tags from Database ID.") )
	
	tag_from_license = models.BooleanField( default = False, verbose_name = _("RFID Tag from License"),
			 help_text=_('Generate RFID tag from license (not database id)'))
	
	ID_CHOICES = [(i, u'{}'.format(i)) for i in range(32)]
	tag_from_license_id = models.PositiveSmallIntegerField( default=0, choices=ID_CHOICES, verbose_name=_('Identifier'),
		help_text=_('Identifier for generating tags from License Code.') )
		
	tag_all_hex = models.BooleanField( default = True, verbose_name = _("RFID Tag all Hex"),
			 help_text=_('Set to True if all tags characters are in [0-9A-F]'))

	RFID_SERVER_HOST_DEFAULT = 'localhost'
	RFID_SERVER_PORT_DEFAULT = 50111
	
	rfid_server_host = models.CharField( max_length = 32, default = RFID_SERVER_HOST_DEFAULT, verbose_name = _('RFID Reader Server Host')  )
	rfid_server_port = models.PositiveIntegerField( default = RFID_SERVER_PORT_DEFAULT, verbose_name = _('RFID Reader Server Port') )
	
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
	server_print_tag_cmd = models.CharField( max_length = 160, default = 'lpr "$1"', verbose_name = _('Cmd used to print Bib Tag (parameter is the PDF file)')  )
	
	cloud_server_url = models.CharField( max_length = 160, blank = True, default = '', verbose_name = _('Cloud Server Url')  )
	
	license_holder_unique_by_license_code = models.BooleanField( default = True, verbose_name = _("License Codes Permanent and Unique"),
		help_text=_('If True, License Holders will be Merged assuming that License Codes are permanent and unique.  Otherwise, ignore and attempt to match by Last, First, Gender and DOB'))
	
	def get_cloud_server_url( self, url_ref ):
		url = self.cloud_server_url
		i = url.find( 'RaceDB' )
		if i > 0:
			url = url[:i+len('RaceDB')] + '/'			
		url += url_ref
		if not url.endswith('/'):
			url += '/'
		return url
	
	@classmethod
	def get_tag_template_default( cls ):
		rs = ''.join( '0123456789ABCDEF'[random.randint(1,15)] for i in range(4))
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
		return u','.join( [self.name, self.description] )
		
	def get_search_text( self ):
		return utils.get_search_text( [self.name, self.description] )
		
	def __str__( self ):
		return self.name
		
	class Meta:
		ordering = ['name']
		verbose_name = _('CategoryFormat')
		verbose_name_plural = _('CategoryFormats')

def init_sequence_last( Class, obj ):
	if not obj.sequence:
		obj.sequence = Class.objects.all().count() + 1
		
def init_sequence_first( Class, obj ):
	if not obj.sequence:
		Class.objects.all().update(sequence = F('sequence')+1)
		obj.sequence = 1
		
class Category(models.Model):
	format = models.ForeignKey( CategoryFormat, db_index = True, on_delete=models.CASCADE )
	code = models.CharField( max_length=32, default='', verbose_name = _('Code') )
	GENDER_CHOICES = (
		(0, _('Men')),
		(1, _('Women')),
		(2, _('Open')),
	)
	gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, default=0, verbose_name=_('Gender') )
	description = models.CharField( max_length=80, default='', blank=True, verbose_name=_('Description') )
	sequence = models.PositiveSmallIntegerField( default=0, verbose_name=_('Sequence') )
	
	def save( self, *args, **kwargs ):
		init_sequence_last( Category, self )
		return super( Category, self ).save( *args, **kwargs )
	
	def make_copy( self, category_format ):
		category_new = self
		
		category_new.pk = None
		category_new.format = category_format
		category_new.save()
		return category_new
	
	def full_name( self ):
		return u', '.join( [self.code, self.get_gender_display(), self.description] )
		
	@property
	def code_gender( self ):
		return u'{} ({})'.format(self.code, self.get_gender_display())
	
	def get_search_text( self ):
		return utils.normalizeSearch(u' '.join( u'"{}"'.format(f) for f in [self.code, self.get_gender_display(), self.description] ) )
		
	def __str__( self ):
		return u'{} ({}) [{}]'.format(self.code, self.description, self.format.name)
		
	class Meta:
		verbose_name = _('Category')
		verbose_name_plural = _("Categories")
		ordering = ['sequence', '-gender', 'code']

#---------------------------------------------------------------------------------
class Discipline(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = 0 )
	
	def save( self, *args, **kwargs ):
		init_sequence_first( Discipline, self )
		return super( Discipline, self ).save( *args, **kwargs )
	
	def __str__( self ):
		return self.name
		
	@staticmethod
	def get_disciplines_in_use():
		return Discipline.objects.filter( pk__in=Competition.objects.all().values_list('discipline', flat=True).distinct() )
		
	class Meta:
		verbose_name = _('Discipline')
		verbose_name_plural = _('Disciplines')
		ordering = ['sequence', 'name']

class RaceClass(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = 0 )
	
	def save( self, *args, **kwargs ):
		init_sequence_first( RaceClass, self )
		return super( RaceClass, self ).save( *args, **kwargs )
	
	def __str__( self ):
		return self.name

	class Meta:
		verbose_name = _('Race Class')
		verbose_name_plural = _('Race Classes')
		ordering = ['sequence', 'name']

class NumberSet(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	sequence = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Sequence'), default = 0 )

	reRangeExcept = re.compile( r'[^\d,-]' )
	range_str = models.TextField( default='', blank = True, verbose_name = _('Ranges') )
	
	sponsor = models.CharField( max_length = 80, default = '', blank = True, verbose_name  = _('Sponsor') )
	description = models.CharField( max_length = 80, default = '', blank = True, verbose_name = _('Description') )
	
	def get_range_events( self ):
		if not self.range_str:
			return []
		range_events = []
		for r in self.range_str.split(','):
			if r.startswith('-'):
				v = -1
				r = r[1:]
			else:
				v = 1
			if not r:
				continue
				
			try:
				a, b = r.split('-')[:2]
			except ValueError:
				a = b = r
			
			try:
				a, b = int(a), int(b)
			except ValueError:
				continue
			
			range_events.append( (a, v) )
			range_events.append( (b+1, -v) )
		
		range_events.sort()
		return range_events
	
	def get_bib_max_count( self, bib, range_events = None  ):
		range_events = range_events or self.get_range_events()
		if not range_events:
			return 1
		count = 0
		for a, v in range_events:
			if a > bib:
				break
			count += v
		return max(0, count)
		
	def is_bib_valid( self, bib, range_events = None ):
		return self.get_bib_max_count(bib, range_events)  > 0
		
	def get_bib_in_use( self, bib ):
		return self.numbersetentry_set.filter(bib=bib).count()
		
	def get_bib_available( self, bib ):
		return self.get_bib_max_count(bib) - self.get_bib_in_use(bib)
	
	def get_bib_max_count_all( self ):
		range_events = self.get_range_events()
		if not range_events:
			return defaultdict( lambda: 1 )
		
		counts = defaultdict( int )
		c = 0
		for i, (bib, v) in enumerate(range_events):
			try:
				bib_next = range_events[i+1][0]
			except IndexError:
				break
			c += v
			if c > 0:
				for bib in range(bib, bib_next):
					counts[bib] = c
		return counts
	
	def get_bib_available_all( self, bib_query=None ):
		bib_used = self.numbersetentry_set.filter( bib_query ) if bib_query else self.numbersetentry_set.all()
		bib_used = bib_used.values_list('bib').annotate(Count('bib'))
		bib_available_all = self.get_bib_max_count_all()
		for bib, used in bib_used:
			bib_available_all[bib] -= used
		return bib_available_all
	
	def save( self, *args, **kwargs ):
		init_sequence_first( NumberSet, self )
		self.range_str = self.reRangeExcept.sub( u'', self.range_str )
		return super( NumberSet, self ).save( *args, **kwargs )
		
	def get_bib( self, competition, license_holder, category, category_numbers_set=None ):
		numbers = None
		if category_numbers_set:
			numbers = category_numbers_set
		else:
			category_numbers = competition.get_category_numbers( category )
			if category_numbers:
				numbers = category_numbers.get_numbers()
		
		if numbers:
			for bib in self.numbersetentry_set.filter(
					license_holder=license_holder, date_lost=None ).order_by('bib').values_list('bib', flat=True):
				if bib in numbers:
					return bib
		return None
	
	def bib_owners( self, bib ):
		return set( self.numbersetentry_set.filter(bib=bib) )
	
	def assign_bib( self, license_holder, bib ):
		if not bib:
			return True
		
		# Check if this license_holder already has this bib assigned, or lost it.
		with transaction.atomic():
			nse = self.numbersetentry_set.filter( license_holder=license_holder, bib=bib ).first()
			if nse:
				if nse.date_lost is not None:
					nse.date_lost = None
					nse.save()
				return True

		# Check if this bib is available.  If so, take it.
		with transaction.atomic():
			if self.get_bib_available(bib) > 0:
				NumberSetEntry( number_set=self, license_holder=license_holder, bib=bib ).save()
				return True
			
		# The bib is unavailable (if invalid).
		# Try to take one that was lost (presumably found), or take it from someone else.
		# If the bib is invalid, do not assign it, and return False.
		with transaction.atomic():
			nse = self.numbersetentry_set.filter( bib=bib, date_lost__isnull=True ).first() or self.numbersetentry_set.filter( bib=bib ).first()
			if not nse:
				return False
			nse.license_holder = license_holder
			nse.date_issued = datetime.date.today()
			nse.date_lost = None
			nse.save()
		
		return True
	
	def set_lost( self, bib, license_holder=None, date_lost=None ):
		if bib is None:
			return
		
		q1 = Q( bib=bib )
		if license_holder:
			q1 &= Q( license_holder=license_holder )
		q2 = Q( date_lost__isnull=True )
		if date_lost:
			q2 |= Q( date_lost__gte=date_lost )
		
		nse = self.numbersetentry_set.filter(q1).filter(q2).first()
		if nse:
			nse.date_lost = date_lost or timezone.localtime(timezone.now()).date()
			nse.save()
	
	def return_to_pool( self, bib, license_holder=None ):
		# If we know the license holder, everything is specified.
		if license_holder:
			self.numbersetentry_set.filter( bib=bib, license_holder=license_holder ).delete()
			return True
			
		# If there is only one possibility for the bib, return it.
		if self.get_bib_max_count(bib) == 1 or self.get_bib_in_use(bib) == 1:
			self.numbersetentry_set.filter( bib=bib ).delete()
			return True
		
		# If this bib was given to two riders and we don't know which one we are returning.
		# Do nothing - FIXLATER.
		return False
	
	def __str__( self ):
		return self.name
	
	def validate( self ):
		# Nulls sort to the beginning.  If we have a lost bib it will have a date_lost.
		# We want to keep as many lost entries as we can, so we delete everything but the last values.
		range_events = self.get_range_events()
		duplicates = defaultdict( list )
		for nse in self.numbersetentry_set.order_by('bib', 'date_lost'):
			duplicates[nse.bib].append( nse.pk )
		for bib, pks in duplicates.items():
			bib_max_count = self.get_bib_max_count(bib, range_events)
			if len(pks) > bib_max_count:
				NumberSetEntry.objects.filter( pk__in=pks[:-bib_max_count] ).delete()
	
	class Meta:
		verbose_name = _('Number Set')
		verbose_name_plural = _('Number Sets')
		ordering = ['sequence']

#-------------------------------------------------------------------
class SeasonsPass(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	sequence = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Sequence'), default = 0 )

	def save( self, *args, **kwargs ):
		init_sequence_first( SeasonsPass, self )
		return super( SeasonsPass, self ).save( *args, **kwargs )
	
	def __str__( self ):
		return self.name
		
	def clone( self ):
		name_new = None
		for i in range(1, 1000):
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
		if not self.has_license_holder( license_holder ):
			SeasonsPassHolder(seasons_pass=self, license_holder=license_holder).save()
			return True
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
	seasons_pass = models.ForeignKey( 'SeasonsPass', db_index = True, verbose_name = _("Season's Pass"), on_delete=models.CASCADE )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True, verbose_name = _("LicenseHolder"), on_delete=models.CASCADE )
	
	def __str__( self ):
		return u''.join( [u'{}'.format(self.seasons_pass), u': ', u'{}'.format(self.license_holder)] )
	
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
	
	def __str__( self ):
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
	
	def __str__( self ):
		return self.name
	
	class Meta:
		ordering = ['name']
		verbose_name = _('LegalEntity')
		verbose_name_plural = _('LegalEntities')

#-------------------------------------------------------------------
class Competition(models.Model):
	name=models.CharField( max_length=64, verbose_name=_('Name') )
	long_name=models.CharField( max_length=80, default='', blank=True, verbose_name=_('Long Name (Title)') )
	description=models.CharField( max_length=80, default='', blank=True, verbose_name=_('Description') )
	
	number_set=models.ForeignKey( NumberSet, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Number Set') )
	seasons_pass=models.ForeignKey( SeasonsPass, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Season's Pass") )
	
	city=models.CharField( max_length=64, blank=True, default='', verbose_name=_('City') )
	stateProv=models.CharField( max_length=64, blank=True, default='', verbose_name=_('StateProv') )
	country=models.CharField( max_length=64, blank=True, default='', verbose_name=_('Country') )
	
	category_format=models.ForeignKey( 'CategoryFormat', verbose_name=_('Category Format'), on_delete=models.CASCADE )
	
	organizer=models.CharField( max_length=64, verbose_name=_('Organizer') )
	organizer_contact=models.CharField( max_length=64, blank=True, default='', verbose_name=_('Organizer Contact') )
	organizer_email=models.EmailField( blank=True, verbose_name=_('Organizer Email') )
	organizer_phone=models.CharField( max_length=22, blank=True, default='', verbose_name=_('Organizer Phone') )
	
	start_date=models.DateField( db_index=True, verbose_name=_('Start Date') )
	number_of_days=models.PositiveSmallIntegerField( default=1, verbose_name=_('Number of Days') )
	
	discipline=models.ForeignKey( Discipline, verbose_name=_("Discipline"), on_delete=models.CASCADE )
	race_class=models.ForeignKey( RaceClass, verbose_name=_("Race Class"), on_delete=models.CASCADE )
	
	using_tags=models.BooleanField( default=False, verbose_name=_("Using Tags/Chip Reader") )
	use_existing_tags=models.BooleanField( default=True, verbose_name=_("Use Competitor's Existing Tags") )
	do_tag_validation=models.BooleanField( default=True, verbose_name=_("Do Tag Validation") )
	
	DISTANCE_UNIT_CHOICES=(
		(0, _('km')),
		(1, _('miles')),
	)
	distance_unit=models.PositiveSmallIntegerField(choices=DISTANCE_UNIT_CHOICES, default=0, verbose_name=_('Distance Unit') )
	
	ftp_host=models.CharField( max_length=80, default='', blank=True, verbose_name=_('FTP Host') )
	ftp_user=models.CharField( max_length=80, default='', blank=True, verbose_name=_('FTP User') )
	ftp_password=models.CharField( max_length=64, default='', blank=True, verbose_name=_('FTP Password') )
	ftp_path=models.CharField( max_length=256, default='', blank=True, verbose_name=_('FTP Path') )
	
	ftp_upload_during_race=models.BooleanField( default=False, verbose_name=_("Live FTP Update During Race") )
	
	show_signature=models.BooleanField( default=True, verbose_name=_("Show Signature in Participant Edit Screen") )
	
	ga_tracking_id=models.CharField( max_length=20, default='', blank=True, verbose_name=_('Google Analytics Tracking ID') )
	
	report_labels=models.ManyToManyField( ReportLabel, blank=True, verbose_name=_('Report Labels') )
	
	legal_entity=models.ForeignKey( LegalEntity, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Legal Entity') )
	
	RECURRING_CHOICES=(
		( 0, '-'),
		( 7, _('Every Week')),
		(14, _('Every 2 Weeks')),
		(21, _('Every 3 Weeks')),
		(28, _('Every 4 Weeks')),
	)
	recurring = models.PositiveSmallIntegerField(choices=RECURRING_CHOICES, default=0, verbose_name=_('Recurring') )
	
	bib_label_print = models.BooleanField( default=False, verbose_name=_("1 Bib Label Print"), help_text=_('1 bib on 1 label') )
	bibs_label_print = models.BooleanField( default=False, verbose_name=_("2 Bibs Label Print"), help_text=_('2 bibs on 2 labels') )
	bibs_laser_print = models.BooleanField( default=False, verbose_name=_("2 Bibs Laser Print"), help_text=_('2 bibs on one page') )
	shoulders_label_print = models.BooleanField( default=False, verbose_name=_("2 Shoulders Label Print"), help_text=_('2 numbers on 2 labels') )
	frame_label_print = models.BooleanField( default=False, verbose_name=_("2 Frame Label Print"), help_text=_('2 frame numbers on 2 labels') )
	frame_label_print_1 = models.BooleanField( default=False, verbose_name=_("1 Frame Label Print"), help_text=_('1 frame number on 1 label') )
	
	license_check_note = models.CharField( max_length=240, default='', blank=True, verbose_name=_('License Check Note') )
	
	report_label_license_check = models.ForeignKey( ReportLabel, blank=True, null=True, on_delete=models.SET_NULL,
		related_name='+',	# no related name.
		verbose_name=_('Report Label License Check'),
		help_text=_('Previous Competitions considered for License Check must have this label'),
	)
	
	@property
	def title( self ):
		return self.long_name or self.name
	
	@property
	def any_print( self ):
		return self.bib_label_print or self.bibs_label_print or self.bibs_laser_print or self.shoulders_label_print or self.frame_label_print or self.frame_label_print_1
	
	def get_filename_base( self ):
		return utils.cleanFileName(u'{}-{}'.format( self.name, self.start_date.strftime('%Y-%m-%d'))).replace(' ', '-')
	
	@property
	def speed_unit_display( self ):
		return 'km/h' if self.distance_unit == 0 else 'mph'
	
	@property
	def report_labels_text( self ):
		return u', '.join( r.name for r in self.report_labels.all() )
		
	@property
	def has_results( self ):
		return ResultMassStart.objects.filter(event__competition=self).exists() or ResultTT.objects.filter(event__competition=self).exists()
	
	@property
	def last_event_date_time( self ):
		date_times = []
		e = EventMassStart.objects.filter(competition=self).order_by('-date_time').first()
		if e:
			date_times.append( e.date_time )
		e = EventTT.objects.filter(competition=self).order_by('-date_time').first()
		if e:
			date_times.append( e.date_time )
		return max( date_times ) if date_times else None
	
	@property
	def first_event_date_time( self ):
		date_times = []
		e = EventMassStart.objects.filter(competition=self).order_by('date_time').first()
		if e:
			date_times.append( e.date_time )
		e = EventTT.objects.filter(competition=self).order_by('date_time').first()
		if e:
			date_times.append( e.date_time )
		return min( date_times ) if date_times else None
	
	@property
	def first_last_event_date_time( self ):
		events = self.get_events()
		return (min(e.date_time for e in events), max(e.date_time for e in events)) if events else (None, None)
	
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
			return format_lazy( u'{}'*len(types), *types )
		return u''
	
	def to_local_speed( self, kmh ):
		return kmh if self.distance_unit == 0 else kmh * 0.621371
		
	def to_local_distance( self, km ):
		return km if self.distance_unit == 0 else km * 0.621371
		
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
		category_numbers = list(self.categorynumbers_set.all())
		event_mass_starts = list(self.eventmassstart_set.all())
		event_tts = list(self.eventtt_set.all())
		report_labels = list( self.report_labels.all() )
		category_options = list( self.competitioncategoryoption_set.all() )
	
		start_date_old, start_date_new = self.start_date, timezone.localtime(timezone.now()).date()
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
		for cco in category_options:
			cco.make_copy( competition_new )
		
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
	
	reMatchLeadingZeros = re.compile( '^0| 0' )
	def fix_date_leading_zeros( self, s ):
		return self.reMatchLeadingZeros.sub(' ', s).strip()
	
	def is_finished( self, dNow=None ):
		if not dNow:
			dNow = datetime.date.today()
		return self.start_date + datetime.timedelta(days=(self.number_of_days or 1)-1) < dNow
	
	@property
	def date_range_str( self ):
		sd = self.start_date
		ed = self.finish_date
		if sd == ed:
			return self.fix_date_leading_zeros(sd.strftime('%b %d, %Y'))
		if sd.month == ed.month and sd.year == ed.year:
			return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%b %d'), ed.strftime('%d, %Y') ))
		if sd.year == ed.year:
			return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%b %d'), ed.strftime('%b %d, %Y') ))
		return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%b %d, %Y'), ed.strftime('%b %d, %Y') ))
	
	@property
	def date_range_year_str( self ):
		sd = self.start_date
		ed = self.finish_date
		if sd == ed:
			return self.fix_date_leading_zeros(sd.strftime('%Y %b %d'))
		if sd.month == ed.month and sd.year == ed.year:
			return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%Y %b %d'), ed.strftime('%d') ))
		if sd.year == ed.year:
			return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%Y %b %d'), ed.strftime('%b %d') ))
		return self.fix_date_leading_zeros(u'{}-{}'.format( sd.strftime('%Y %b %d'), ed.strftime('%Y %b %d') ))
	
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
		return u' '.join( [self.name, self.organizer] )
		
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
		
	def sync_tags( self ):
		if self.using_tags and self.use_existing_tags:
			qtag = self.get_participants().exclude( Q(tag=F('license_holder__existing_tag')) & Q(tag2=F('license_holder__existing_tag2')) )
			if qtag.exists():
				qtag.update( tag=None, tag2=None )
				with transaction.atomic():
					for p in qtag.select_related('license_holder'):
						p.tag  = p.license_holder.existing_tag
						p.tag2 = p.license_holder.existing_tag2
						p.save()
				return True
		return False
			
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
		if not isinstance(categories, set):
			categories = set(categories)
		if len(categories) > 1:
			# Check if the set of categories would cause racing in the same event simultaneously in different waves.
			for e in self.get_events():
				event_categories = e.get_categories_with_wave()
				compete_categories = categories & set( event_categories )
				if len(compete_categories) > 1:
					return True, e, event_categories
		return False, None, None
	
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
			self.number_set.validate()
			
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
				
			for bibs in nses.values():
				bibs.sort()
			
			with transaction.atomic():
				for p in participants:
					bib_category = None
					if p.category:
						for bib in nses[p.license_holder.pk]:
							if p.category.pk in category_nums and bib in category_nums[p.category.pk]:
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
			self.number_set.validate()
	
	def prereg_detect( self ):
		off_site_count = prereg_count = total_count = 0
		off_site_count_run, off_site_count_run_max, off_site_prereg_count = 1, 5, 0
		prev = None
		
		#--------------------------------------------------------------------------
		# off_site registration is defined by registration through Excel import.
		# Excel import will have registration_timestamp of less than 0.2 seconds.
		# off_site registration is also pre-registration even if the preregistered flag is not set.
		#
		for registration_timestamp, preregistered in self.get_participants().order_by('registration_timestamp').values_list(
				'registration_timestamp', 'preregistered'):
			cur = registration_timestamp
			if prev:
				if (cur-prev).total_seconds() < 0.2:
					off_site_count_run += 1								# Track a run of automatic imports.
				else:
					if off_site_count_run >= off_site_count_run_max:	# Process the run.
						off_site_count += off_site_count_run
						prereg_count += off_site_count_run - off_site_prereg_count
					off_site_prereg_count = 0
					off_site_count_run = 1								# Reset the run to the current participant.
			prev = cur
			
			if preregistered:
				prereg_count += 1
				off_site_prereg_count += 1
			total_count += 1
		
		# Finalize run processing.
		if off_site_count_run >= off_site_count_run_max:
			off_site_count += off_site_count_run
			prereg_count += off_site_count_run - off_site_prereg_count
		
		on_site = total_count - off_site_count
		
		seasons_pass_count = SeasonsPassHolder.objects.filter(
			seasons_pass=self.seasons_pass,
			license_holder__pk__in=self.get_participants().values('license_holder__pk'),
		).values('pk').distinct().count() if self.seasons_pass else 0
		seasons_pass_total = self.get_participants().values('license_holder__pk').distinct().count()
		
		return {
			'prereg':				prereg_count,
			'on_site':				on_site,
			'total':				total_count,
			'prereg_percent':		float(prereg_count)/float(total_count) if total_count else 0.0,
			'on_site_percent':		float(on_site)/float(total_count) if total_count else 0.0,
			'seasons_pass':			seasons_pass_count,
			'seasons_pass_percent':	float(seasons_pass_count)/float(seasons_pass_total) if seasons_pass_total else 0.0,
			'seasons_pass_total':	seasons_pass_total,
		}
	
	def seasons_pass_holders_count( self ):
		return SeasonsPassHolder.objects.filter(
			seasons_pass=self.seasons_pass,
			license_holder__pk__in=self.get_participants().values('license_holder__pk'),
		).count() if self.seasons_pass else 0
		
	class Meta:
		verbose_name = _('Competition')
		verbose_name_plural = _('Competitions')
		ordering = ['-start_date', 'name']

def get_bib_query( bibs ):
	if not bibs:
		return Q( bib=999999 )
		
	bibs = sorted( set(bibs) )
	standalone_bibs = []	# List of individual bibs not in a range.

	def add_range( query, a, b ):
		if a == b:
			standalone_bibs.append( a )
			return query
		try:
			return query | Q(bib__range=(a,b))
		except TypeError:
			return Q(bib__range=(a,b))

	query = None
	a = b = bibs[0]
	for n in bibs[1:]:
		if n - 1 == b: # Part of the group, bump the end
			b = n
		else: # Not part of the group, process current group and start a new
			query = add_range( query, a, b )
			a = b = n
	query = add_range( query, a, b )
	
	if standalone_bibs:
		q = Q( bib=standalone_bibs[0] ) if len(standalone_bibs) == 1 else Q( bib__in=standalone_bibs )
		try:
			query |= q
		except TypeError:
			query = q
	
	return query

def validate_range_str( range_str ):
	r = range_str.upper()
	r = re.sub( r'\s', ',', r, flags=re.UNICODE )	# Replace spaces with commas.
	r = re.sub( r'[^0123456789,-]', '', r )			# Remove invalid characters.
	r = re.sub( r',,+', ',', r )						# Remove repeated commas.

	if r.startswith( ',' ):
		r = r[1:]
	while r.endswith( ',' ) or r.endswith( '-' ):
		r = r[:-1]
	
	num_max = 99999
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
			pairs.append( exclude + u'{}'.format(n) )
		elif len(pair) >= 2:
			try:
				nBegin = int(pair[0])
			except:
				continue
			try:
				nEnd = int(pair[1])
			except:
				continue
			nBegin = min( nBegin, num_max )
			nEnd = min( max(nBegin,nEnd), num_max )
			pairs.append( exclude + u'{}'.format(nBegin) + u'-' + u'{}'.format(nEnd) )
	
	return u', '.join( pairs )

def get_numbers( range_str ):
	include = set()
	for p in range_str.split(','):
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
		elif len(pair) >= 2:
			nBegin, nEnd = [int(v) for v in pair[:2]]
			nBegin, nEnd = max(nBegin, 1), min(nEnd, 99999)
			if exclude:
				include.difference_update( range(nBegin, nEnd+1) )
			else:
				include.update( range(nBegin, nEnd+1) )
	
	return include
	
class CategoryNumbers( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True, on_delete=models.CASCADE )
	categories = models.ManyToManyField( Category )
	range_str = models.TextField( default = '1-99,120-129,-50-60,181,-87', verbose_name=_('Range') )
	
	numCache = None
	
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
		
		category_numbers_new.categories.set( categories )
		return category_numbers_new
	
	def validate( self ):
		self.range_str = validate_range_str( self.range_str )
		return self.range_str
	
	def getNumbersWorker( self ):
		self.validate()
		include = get_numbers( self.range_str )
		if self.competition.number_set:
			number_set = self.competition.number_set
			range_events = number_set.get_range_events()
			is_bib_valid = number_set.is_bib_valid
			include = set( bib for bib in include if is_bib_valid(bib, range_events) )
		include.discard( 0 )
		return include
	
	def get_numbers( self ):
		if self.numCache is None or getattr(self, 'range_str_cache', None) != self.range_str:
			self.numCache = self.getNumbersWorker()
			self.range_str_cache = self.range_str
		return self.numCache
		
	def get_bib_query( self ):
		return get_bib_query( self.get_numbers() )
	
	def __contains__( self, n ):
		return n in self.get_numbers()
		
	def add_bib( self, n ):
		if n not in self:
			self.range_str += u', {}'.format( n )
			
	def remove_bib( self, n ):
		if n in self:
			self.range_str += u', -{}'.format( n )
		
	def save(self, *args, **kwargs):
		self.validate()
		return super(CategoryNumbers, self).save( *args, **kwargs )
	
	class Meta:
		verbose_name = _('CategoryNumbers')
		verbose_name_plural = _('CategoriesNumbers')
		
def get_num_nationalities( participants ):
	return participants.exclude(license_holder__nation_code='').values('license_holder__nation_code').distinct().count()

class Event( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True, on_delete=models.CASCADE )
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
		return mark_safe( u'<br/>'.join( escape(v) for v in self.note.split(u'\n') ) ) if self.note else u''
	
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
		return self.wave_set if self.event_type == 0 else self.wavett_set
		
	def get_custom_category_set( self ):
		return self.customcategorymassstart_set if self.event_type == 0 else self.customcategorytt_set
		
	def get_categories( self ):
		return list(self.get_categories_query())
	
	def get_custom_categories( self ):
		return list(self.get_custom_category_set().all().order_by('sequence'))
	
	def get_wave_for_category( self, category ):
		return self.get_wave_set().filter(categories=category).first()
	
	def get_result_class( self ):
		raise NotImplementedError("Please Implement this method")
		
	def get_race_time_class( self ):
		raise NotImplementedError("Please Implement this method")
		
	def get_custom_category_class( self ):
		raise NotImplementedError("Please Implement this method")
			
	def get_results( self ):
		return self.get_result_class().objects.filter( event=self )
		
	def add_laps_to_results_query( self, results ):
		return results.annotate( laps=Count(self.get_race_time_class().__name__.lower()) )

	def has_results( self ):
		return self.get_results().exists()
		
	def get_prereg_results( self ):
		for w in self.get_wave_set().all():
			for r in w.get_prereg_results():
				yield r
	
	def get_results_num_starters( self ):
		return self.get_results().exclude(status=Result.cDNS).count()
		
	def get_type_abbrev( self ):
		if self.event_type == 0:
			return ''
		elif self.event_type == 1:
			return _('(TT)')
		else:
			return ''
	
	def get_results_num_nationalities( self ):
		return self.get_results().exclude(
			status=Result.cDNS).exclude(
			participant__license_holder__nation_code='').values_list('participant__license_holder__nation_code').distinct().count()
	
	def reg_is_late( self, reg_closure_minutes, registration_timestamp ):
		if reg_closure_minutes < 0:
			return False
		delta = self.date_time - registration_timestamp
		return delta.total_seconds()/60.0 < reg_closure_minutes
	
	def make_copy( self, competition_new, start_date_old, start_date_new ):
		pk_old = self.pk
		waves = list(self.get_wave_set().all())
		custom_categories = list(self.get_custom_categories())
		
		time_diff = self.date_time - datetime.datetime.combine(
			start_date_old, datetime.time(0,0,0)
		).replace(tzinfo = get_default_timezone())
				
		event_new = self
		event_new.id = None
		event_new.pk = None
		event_new.competition = competition_new
		event_new.date_time = datetime.datetime.combine(
			start_date_new, datetime.time(0,0,0)).replace(tzinfo = get_default_timezone()) + time_diff
		event_new.option_id = 0		# Ensure the option_id gets reset if necessary.
		event_new.save()
		
		for w in waves:
			w.make_copy( event_new )
			
		for cc in custom_categories:
			cc.make_copy( event_new )
			
		# If this event is in a series, add the new event to the series also.
		q = Q(event_mass_start__pk=pk_old) if self.event_type == 0 else Q(event_tt__pk=pk_old)
		for ce in SeriesCompetitionEvent.objects.filter( q ):
			ce.pk = None
			ce.event = event_new
			ce.save()
		
		return event_new
	
	def get_duplicate_bibs( self ):
		duplicates = []
		for w in self.get_wave_set().all():
			bibParticipant = {}
			for c in w.categories.all():
				for p in Participant.objects.filter( competition=self.competition, role=Participant.Competitor, category=c, bib__isnull=False ):
					if p.bib in bibParticipant:
						s = format_lazy( u'{}: {} ({}) and {} ({}) {} {}',
								w.name, bibParticipant[p.bib].name, bibParticipant[p.bib].category.code,
								p.name, p.category.code,
								_('have duplicate Bib'), p.bib
							)
						duplicates.append( s )
					else:
						bibParticipant[p.bib] = p
		return duplicates
		
	#----------------------------------------------------------------------------------------------------
	
	def get_potential_duplicate_bibs( self ):
		category_numbers = set()
		for c in self.get_categories_query():
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
			'date_time': u'{}'.format(server_date_time),
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
		return u'<ol><li>' + u'</li><li>'.join( u'<strong>{}</strong>, {}<br/>{}'.format(
			w.name, w.get_details_html(True), 
			w.category_count_html
		) for w in self.get_wave_set().all() ) + u'</li></ol>'
	
	@property
	def custom_category_text_html( self ):
		ccs = self.get_custom_categories()
		if not ccs:
			return u''
		return u'<ol><li>' + u'</li><li>'.join( u'<strong>{}</strong>'.format(cc.name) for cc in ccs ) + u'</li></ol>'
	
	def get_categories_query( self ):
		q = None
		for w in self.get_wave_set().all():
			if q is None:
				q = w.categories.all()
			else:
				q |= w.categories.all()
		return q or Category.objects.none()
	
	def get_participants( self ):
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=self.get_categories_query(),
			).select_related('license_holder','team')
		else:
			return Participant.objects.filter(
				pk__in=ParticipantOption.objects.filter(
					competition=self.competition,
					option_id=self.option_id,
					participant__role=Participant.Competitor,
					participant__competition=self.competition,
					participant__category__in=self.get_categories_query(),
				).values_list('participant__pk', flat=True)
			).select_related('license_holder','team')

	def get_num_nationalities( self ):
		return get_num_nationalities( self.get_participants() )
			
	def has_participants( self ):
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=self.get_categories_query(),
			).exists()
		else:
			return ParticipantOption.objects.filter(
				competition=self.competition,
				option_id=self.option_id,
				participant__role=Participant.Competitor,
				participant__competition=self.competition,
				participant__category__in=self.get_categories_query(),
			).exists()
		
	def get_participant_count( self ):
		if not self.option_id:
			return Participant.objects.filter(
				competition=self.competition,
				role=Participant.Competitor,
				category__in=self.get_categories_query(),
			).count()
		else:
			return ParticipantOption.objects.filter(
				competition=self.competition,
				option_id=self.option_id,
				participant__role=Participant.Competitor,
				participant__competition=self.competition,
				participant__category__in=self.get_categories_query(),
			).count()
			
	def get_ineligible( self ):
		return (self.get_participants()
			.exclude( license_holder__eligible=True )
			.exclude( Q(license_holder__ineligible_on_date_time__isnull=False) & Q(license_holder__ineligible_on_date_time__lt=timezone.now()) )
			.order_by('license_holder__search_text')
		)
			
	def __str__( self ):
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
						competition=self.competition, role=Participant.Competitor, category__in=self.get_categories_query()
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
	def __init__( self, *args, **kwargs ):
		kwargs['event_type'] = 0
		super( EventMassStart, self ).__init__( *args, **kwargs )
		
	def get_result_class( self ):
		return ResultMassStart
		
	def get_race_time_class( self ):
		return RaceTimeMassStart
	
	def get_custom_category_class( self ):
		return CustomCategoryMassStart
		
	def get_series( self ):
		for ce in SeriesCompetitionEvent.objects.filter( event_mass_start=self ).exclude( series__callup_max=0 ).order_by('series__sequence'):
			if ce and not set( self.get_categories() ).isdisjoint( ce.series.get_categories() ):
				return ce.series
		return None
	
	win_and_out = models.BooleanField( default = False, verbose_name = _("Win and Out") )

	class Meta:
		verbose_name = _('Mass Start Event')
		verbose_name_plural = _('Mass Starts Event')

class WaveBase( models.Model ):
	name = models.CharField( max_length = 32 )
	categories = models.ManyToManyField( Category, verbose_name = _('Categories') )
	
	# distance is always stored in km.
	distance = models.FloatField( null = True, blank = True, verbose_name = _('Distance') )
	laps = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Laps') )
	
	max_participants = models.PositiveIntegerField( null = True, blank = True, verbose_name = _('Max Participants') )
	
	rank_categories_together = models.BooleanField( default=False, verbose_name = _("Rank Categories Together"),
		help_text=_('If False, Categories in the Wave will be ranked seperately.  If True, all Categories in the Wave will be ranked together.')
	)
	
	@property
	def distance_unit( self ):
		return self.event.competition.get_distance_unit_display() if self.event else ''
	
	def get_category_format( self ):
		return self.event.competition.category_format
	
	def make_copy( self, event_new ):
		categories = self.categories.all()
		wave_new = self
		wave_new.pk = None
		wave_new.id = None
		wave_new.event = event_new
		wave_new.save()
		wave_new.categories.set( categories )
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
		return self.get_participants_unsorted().select_related('category', 'license_holder').order_by('bib')
		
	def get_participants_within_max( self ):
		if not self.max_participants or self.max_participants < 0:
			return self.get_participants()
		with transaction.atomic():
			count = self.get_participant_count()
			if count <= self.max_participants:
				return self.get_participants()
			participants = list(self.get_participants_unsorted().defer('signature').order_by('registration_timestamp','bib')[:self.max_participants])
			participants.sort( key=lambda p: (p.bib or 999999) )
			return participants		
		
	def get_particpants_standby( self ):
		if not self.max_participants or self.max_participants < 0:
			return []
		with transaction.atomic():
			count = self.get_participant_count()
			if count <= self.max_participants:
				return []
			standby = list(self.get_participants_unsorted().defer('signature').order_by('-registration_timestamp','-bib')[:self.max_participants-count])
			standby.reverse()
			return standby
		
	def get_standby_rank( self, participant ):
		standby = self.get_particpants_standby()
		for rank, p in enumerate(standby,1):
			if participant.registration_timestamp < p.registration_timestamp:
				break
			if participant.id == p.id:
				return rank, len(standby)
		return 0, len(standby)
		
	def is_standby( self, participant ):
		return self.get_standby_rank(participant)[0] != 0
		
	def get_num_nationalities( self ):
		return get_num_nationalities( self.get_participants_unsorted() )
	
	def get_results( self, category=None ):
		if category:
			assert self.categories.filter(pk=category.pk).exists()
			return self.event.get_results().filter(participant__category=category).order_by('status','category_rank')
		else:
			return self.event.get_results().filter(participant__category__in=self.categories.all()).order_by('status','wave_rank')

	def has_results( self ):
		return self.get_results().exists()
	
	def get_results_num_starters( self ):
		return self.get_results().exclude(status=Result.cDNS).count()
	
	def get_results_num_nationalities( self ):
		return self.get_results().exclude(
			status=Result.cDNS).exclude(
			participant__license_holder__nation_code='').values_list('participant__license_holder__nation_code').distinct().count()
	
	def get_prereg_results( self, category=None ):
		assert not self.has_results()
		
		RC = self.event.get_result_class()
		if category:
			participants = list( p for p in self.get_participants() if p.category == category )
		else:
			participants = list( self.get_participants() )
		participants.sort( key=operator.attrgetter('license_holder.search_text') )
		
		category_starters = defaultdict( int )
		for p in participants:
			category_starters[p.category_id] += 1
		
		wave_starters = sum( category_starters.values() )
		category_rank = defaultdict( int )
		for pos, p in enumerate(participants, 1):
			category_rank[p.category_id] += 1
			yield RC(
				event=self.event,
				participant=p,
				status=Result.cNP,
				category_rank=category_rank[p.category_id], category_starters=category_starters[p.category_id],
				wave_rank=pos, wave_starters=wave_starters,
			)
			
	@property
	def spots_remaining( self ):
		return None if self.max_participants is None else max(0, self.max_participants - self.get_participant_count())
	
	@property
	def is_full( self ):
		return self.max_participants is not None and self.spots_remaining <= 0
		
	def get_starters_str( self, count=None ):
		count = self.get_participant_count() if count is None else count
		if not self.max_participants:
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
		return u', '.join( category.code_gender for category in sorted(self.categories.all(), key=operator.attrgetter('sequence')) )
	
	def get_category_count( self ):
		category_count = defaultdict( int )
		for p in self.get_participants_unsorted():
			category_count[p.category] += 1
		return [(category, category_count[category]) for category in sorted(self.categories.all(), key=operator.attrgetter('sequence'))]
	
	def get_results_category_count( self ):
		category_count = defaultdict( int )
		for rr in self.get_results():
			category_count[rr.participant.category] += 1
		return [(category, category_count[category]) for category in sorted(self.categories.all(), key=operator.attrgetter('sequence')) if category_count[category] > 0]
	
	@property
	def category_count_text( self ):
		return u', '.join( u'{} {}'.format(category.code_gender, category_count) for category, category_count in self.get_category_count() )
	
	@property
	def category_count_html( self ):
		return u', '.join( u'{} {}'.format(category.code_gender, category_count).replace(u' ', u'&nbsp;') for category, category_count in self.get_category_count() )
	
	@property
	def category_text_html( self ):
		return u'<ol><li>' + u'</li><li>'.join( category.code_gender for category in sorted(self.categories.all(), key=operator.attrgetter('sequence')) ) + u'</li></ol>'
		
	def get_details_html( self, include_starters=False ):
		distance = None
		if self.distance:
			if self.laps:
				distance = self.distance * self.laps
			else:
				distance = self.distance
		s = u', '.join( v for v in (
			u'{}:&nbsp;<strong>{}</strong>'.format(u'Offset', self.start_offset) if include_starters and hasattr(self,'start_offset') else None,
			u'{}:&nbsp;<strong>{}</strong>'.format(u'Start Time', timezone.localtime(self.event.date_time + self.start_offset).strftime('%H:%M:%S')) if include_starters and hasattr(self,'start_offset') else None,
			u'{:.2f}&nbsp;<strong>{}</strong>'.format(distance, self.distance_unit) if distance else None,
			u'{}&nbsp;<strong>{}</strong>'.format(self.laps, u'laps' if self.laps != 1 else u'lap') if self.laps else None,
			u'<strong>{}&nbsp;{}</strong>'.format(self.minutes, u'min') if getattr(self, 'minutes', None) else None,
			u'Rank&nbsp;Together' if getattr(self, 'rank_categories_together', False) else None,
			u'{}:&nbsp;<strong>{}</strong>'.format(u'Starters', self.get_starters_str().replace(' ', '&nbsp;')) if include_starters else None,
		) if v )
		return s
	
	class Meta:
		verbose_name = _('Wave Base')
		verbose_name_plural = _('Wave Bases')
		abstract = True

class Wave( WaveBase ):
	event = models.ForeignKey( EventMassStart, db_index = True, on_delete=models.CASCADE )
	start_offset = DurationField.DurationField( default = duration_field_0, null = True, blank = True, verbose_name = _('Start Offset') )
	
	minutes = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Race Minutes') )
	
	def get_results( self, category = None ):
		return super( Wave, self ).get_results( category ).select_related('participant', 'participant__license_holder')
	
	def get_json( self ):
		self.start_offset = self.start_offset or datetime.timedelta( seconds=0.0 )
		js = super(Wave, self).get_json()
		try:
			seconds = self.start_offset.total_seconds()
		except:
			seconds = self.start_offset
		js['start_offset'] = DurationField.format_seconds( seconds )
		return js
	
	def get_start_time( self ):
		self.start_offset = self.start_offset or datetime.timedelta( seconds=0.0 )
		try:
			return self.event.date_time + self.start_offset
		except TypeError:
			return self.event.date_time + datetime.timedelta(self.start_offset)
	
	class Meta:
		verbose_name = _('Wave')
		verbose_name_plural = _('Waves')
		ordering = ['start_offset', 'name']

class WaveCallup( models.Model ):
	wave = models.ForeignKey( Wave, db_index = True, on_delete=models.CASCADE )
	participant = models.ForeignKey( 'Participant', db_index = True, on_delete=models.CASCADE )
	order = models.PositiveSmallIntegerField( blank = True, default = 9999, verbose_name = _('Callup Order') )
	
	class Meta:
		verbose_name = _('WaveCallup')
		verbose_name_plural = _('WaveCallups')
		ordering = ['order']
	
#-------------------------------------------------------------------------------------
class Team(models.Model):
	name = models.CharField( max_length=128, db_index = True, verbose_name = _('Name') )
	team_code = models.CharField( max_length=16, blank = True, db_index = True, verbose_name = _('Team Code') )
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

	contact = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('Contact') )
	contact_email = models.EmailField( blank = True, verbose_name=_('Contact Email') )
	contact_phone = models.CharField( max_length = 64, blank = True, default = '', verbose_name=_('Contact Phone') )
	
	@property
	def license_holder_pks( self ):
		return (
			set(TeamHint.objects.filter(team=self).values_list('license_holder',flat=True).distinct()) |
			set(Participant.objects.filter(team=self).values_list('license_holder',flat=True).distinct())
		)
	
	@property
	def license_holder_count( self ):
		return len(self.license_holder_pks)
		
	@property
	def license_holders( self ):
		return LicenseHolder.objects.filter( pk__in=self.license_holder_pks )

	def get_team_aliases( self ):
		return u', '.join(u'"{}"'.format(ta.alias) for ta in self.teamalias_set.all())

	def get_team_aliases_html( self ):
		team_aliases = list(self.teamalias_set.all())
		if not team_aliases:
			return u''
		strings = [u'<ul>']
		for ta in team_aliases:
			strings.extend( [u'<li>', escape(ta.alias), u'</li>'] )
		strings.append( u'</ul>' )
		return mark_safe( format_lazy(u'{}'*len(strings), *strings) )

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
		
	def __str__( self ):
		return u'{}, {}'.format(self.name, self.team_type_display())
	
	@staticmethod
	def is_independent_name( team_name ):
		if team_name is None:
			return False
		return team_name.lower() == u'independent'
	
	class Meta:
		verbose_name = _('Team')
		verbose_name_plural = _('Teams')
		ordering = ['search_text']

class TeamAlias(models.Model):
	team = models.ForeignKey( 'Team', db_index=True, on_delete=models.CASCADE )
	alias = models.CharField( max_length = 64, db_index = True, verbose_name = _('Alias') )
	
	@staticmethod
	def alias_conflicts():
		map = defaultdict( set )
		def add_team_name( name, team ):
			key = utils.get_search_text([name])
			map[key].add( team )
		
		for team in  Team.objects.all():
			add_team_name( team.name, team )
		for ta in TeamAlias.objects.all():
			add_team_name( ta.alias, ta.team )
		
		return {k:sorted(v, key = operator.attrgetter('search_text')) for k, v in map if len(v) > 1 }
	
	class Meta:
		verbose_name = _('Team Alias')
		verbose_name_plural = _('Team Aliases')
		ordering = ['team__search_text']

class TeamLookup( object ):
	def __init__( self ):
		self.refresh()
		
	def refresh( self ):
		self.map = { utils.get_search_text([team.name]):team for team in Team.objects.all() }
		for ta in TeamAlias.objects.all():
			self.map[utils.get_search_text([ta.alias])] = ta.team
	
	def __contains__( self, name ):
		if name:
			name = name.strip()
		if not name or Team.is_independent_name(name):
			return True		# Independent
		key = utils.get_search_text([name,])
		return key in self.map
	
	def __getitem__( self, name ):
		if name:
			name = name.strip()
		if not name or Team.is_independent_name(name):
			return None		# Independent.
		key = utils.get_search_text([name,])
		team = self.map.get(key, None)
		if not team:
			team = Team( name = name )
			team.save()
			self.map[utils.get_search_text([team.name])] = team
		return team
		
rePostalCode = re.compile('^[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d$')
def validate_postal_code( postal ):
	postal = (postal or '').replace(' ', '').upper()
	return postal[0:3] + ' ' + postal[3:] if rePostalCode.match(postal) else postal

def random_temp_license( prefix = u'TEMP_'):
	return u'{}{}'.format( prefix, ''.join(random.choice('0123456789') for i in range(15)) )

def format_phone( phone ):
	if len(phone) == len('AAA333NNNN') and phone.isdigit():
		return u'({}) {}-{}'.format(phone[:3], phone[3:6], phone[6:])
	return phone

def flag_html( nation_code ):
	if nation_code and nation_code in uci_country_codes_set:
		flag = '<img src="{}/{}.png"/>'.format(static('flags'), nation_code)
	else:
		flag = nation_code
	return mark_safe(flag)

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
	nation_code = models.CharField( max_length=3, blank=True, default='', verbose_name=_('NatCode') )
	zip_postal = models.CharField( max_length=12, blank=True, default='', verbose_name=_('Zip/Postal') )
	
	email = models.EmailField( blank=True )
	phone = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Phone') )
	
	uci_code = models.CharField( max_length=11, blank=True, default='', db_index=True, verbose_name=_('UCI Code') )
	uci_id = models.CharField( max_length=11, blank=True, default='', db_index=True, verbose_name=_('UCIID') )
	
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
	ineligible_on_date_time = models.DateTimeField( auto_now_add=False, blank=True, null=True, default=None, verbose_name=_('Ineligible Starting at'),
		help_text=_('Date/Time when the License Holder starts to be ineligible.  Defaults to the next day.  If blank, the License Holder will be ineligible immediately.  ') )
	
	emergency_contact_name = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Emergency Contact') )
	emergency_contact_phone = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Emergency Contact Phone') )
	emergency_medical = models.CharField( max_length=128, blank=True, default='',
		verbose_name=_('Medical Alert'), help_text = _('eg. diabetic, drug alergy, etc.') )

	@property
	def is_eligible( self ):
		if self.eligible:
			return True
		if self.ineligible_on_date_time is None:
			return False
		return timezone.now() < self.ineligible_on_date_time
	
	def get_age( self ):
		today = timezone.localtime( timezone.now() ).date()
		return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

	def get_nationality( self ):
		nationality = self.nationality
		if len(nationality) > 24:
			if self.nation_code:
				nationality = self.nation_code
			else:
				nationality = nationality[:24]
		if nationality.upper() == 'CANADA':
			nationality = 'Canada'
		return nationality

	def correct_uci_county_code( self ):
		uci_code_save = self.uci_code
		country_code = self.uci_code[:3].upper()
		if country_code and country_code.isalpha() and country_code != iso_uci_country_codes.get(country_code, country_code):
			country_code = iso_uci_country_codes.get(country_code, country_code)
			
		dob = self.date_of_birth.strftime('%Y%m%d')
		self.uci_code = country_code + dob
		if self.uci_code != uci_code_save:
			self.save()
	
	reUCIID = re.compile( r'[^\d]' )
	def save( self, *args, **kwargs ):
		self.uci_code = (self.uci_code or u'').replace(u' ', '').upper()
		self.uci_id = self.reUCIID.sub( u'', (self.uci_id or u'') )[:11]
		
		self.gender = self.gender or 0
		
		if not( self.existing_bib is None or isinstance(self.existing_bib, int) ):
			self.existing_bib = None
		
		for f in ('last_name', 'first_name', 'city', 'state_prov', 'nationality', 'nation_code'):
			setattr( self, f, (getattr(self, f) or '').strip() )
		for f in ['license_code', 'existing_tag', 'existing_tag2']:
			setattr( self, f, fixNullUpper(getattr(self, f)) )
				
		# Fix nation code.
		if not self.nation_code:
			self.nation_code = u''
			if self.uci_code and country_from_ioc(self.uci_code[:3]):
				self.nation_code = self.uci_code[:3].upper()
			elif ioc_from_country(self.nationality):
				self.nation_code = ioc_from_country(self.nationality)
		else:
			self.nation_code = self.nation_code.upper()
			
			# Check for ISO country code and convert to IOC country code.
			if self.nation_code != iso_uci_country_codes.get(self.nation_code, self.nation_code):
				self.nation_code = iso_uci_country_codes.get(self.nation_code, self.nation_code)
		
			if self.nation_code not in uci_country_codes_set:
				self.nation_code = u''
		
		if self.nation_code and country_from_ioc(self.nation_code):
			self.nationality = country_from_ioc(self.nation_code)
		else:
			self.nation_code = u''
			
		if not self.emergency_contact_name or self.emergency_contact_name.startswith('0'):
			self.emergency_contact_name = u''
		if not self.emergency_contact_phone or self.emergency_contact_phone == '0':
			self.emergency_contact_phone = u''
		
		# Fix up date of birth.
		if self.date_of_birth != invalid_date_of_birth:
			if self.uci_code and len(self.uci_code) == 3 and not self.uci_code.isdigit():
				self.uci_code += self.date_of_birth.strftime( '%Y%m%d' )
				
			if not self.uci_code and ioc_from_country(self.nationality):
				self.uci_code = '{}{}'.format( ioc_from_country(self.nationality), self.date_of_birth.strftime('%Y%m%d') )
		
		# Fix up UCI code.
		if len(self.uci_code) == 11:
			country_code = self.uci_code[:3]
			if country_code != iso_uci_country_codes.get(country_code, country_code):
				self.uci_code = '{}{}'.format( iso_uci_country_codes.get(country_code, country_code), self.uci_code[3:] )
		
		if not self.state_prov and self.license_code and self.license_code[:2] in province_codes:
			self.state_prov = province_codes[self.license_code[:2]]
		
		try:
			self.license_code = self.license_code.strip().lstrip('0')
		except Exception as e:
			pass
		
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
	def has_results( self ):
		return ResultMassStart.objects.filter(participant__license_holder=self).exists() or ResultTT.objects.filter(participant__license_holder=self).exists()
		
	@property
	def uci_country( self ):
		if not self.uci_code:
			return None
		return ioc_from_code( self.uci_code )
		
	@property
	def nation_code_error( self ):
		if not self:
			return None
			
		if not self.nation_code:
			return _(u'missing')
			
		if self.nation_code not in uci_country_codes_set:
			return _(u'invalid nation code')	
		return None
	
	@property
	def uci_id_error( self ):
		if not self or not self.uci_id:
			return None
			
		self.uci_id = u'{}'.format(self.uci_id).upper().replace(u' ', u'')
		
		if not self.uci_id.isdigit():
			return _(u'uci id must be all digits')
		
		if self.uci_id.startswith('0'):
			return _(u'uci id must not start with zero')
		
		if len(self.uci_id) != 11:
			return _(u'uci id must be 11 digits')
			
		if int(self.uci_id[:-2]) % 97 != int(self.uci_id[-2:]):
			return _(u'uci id check digit error')
		return None
	
	@property
	def uci_code_error( self ):
		if not self or not self.uci_code:
			return None
			
		self.uci_code = u'{}'.format(self.uci_code).upper().replace(u' ', u'')
		
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
			return u'{}'.format(e)
		
		if d != self.date_of_birth:
			return _(u'inconsistent with date of birth')
		
		age = timezone.localtime(timezone.now()).date().year - d.year
		if age < self.MinAge:
			return _(u'date too recent')
		if age > self.MaxAge:
			return _(u'date too early')
		return None

	@property
	def date_of_birth_error( self ):
		if not self or not self.date_of_birth:
			return None
		age = timezone.localtime(timezone.now()).date().year - self.date_of_birth.year
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
		return self.uci_id_error or self.license_code_error
		
	def __str__( self ):
		return '{}, {} ({}, {}, {}, {})'.format(
			self.last_name.upper(), self.first_name,
			self.date_of_birth.isoformat(), self.get_gender_display(),
			self.nation_code, self.license_code
		)
		
	def full_name( self ):
		return u"{}, {}".format(self.last_name.upper(), self.first_name)
		
	def full_license( self ):
		return u', '.join( f for f in (self.uci_id, self.license_code) if f )
		
	def get_location( self ):
		return u', '.join( f for f in (self.city, get_abbrev(self.state_prov)) if f )
	
	@property
	def first_last( self ):
		return u' '.join( f for f in (self.first_name, self.last_name) if f )
		
	@property
	def first_last_short( self ):
		return u'. '.join( f for f in (self.first_name[:1], self.last_name) if f )
		
	def get_search_text( self ):
		return utils.get_search_text( [
				self.last_name, self.first_name,
				self.license_code,
				self.nation_code, self.uci_id,
				self.state_prov, self.city,
				self.existing_tag, self.existing_tag2
			]
		)
		
	@staticmethod
	def auto_create_tags():
		system_info = SystemInfo.get_singleton()
		tags = set()
		with BulkSave() as bs:
			for lh in LicenseHolder.objects.all():
				tag = lh.get_unique_tag( system_info, False )
				while tag in tags:
					tag = get_id( system_info.tag_bits )
				tags.add( tag )
				lh.existing_tag = tag
				lh.existing_tag2 = None
				bs.append( lh )
	
	def get_unique_tag( self, system_info=None, validate=True ):
		if not system_info:
			system_info = SystemInfo.get_singleton()
		
		if system_info.tag_creation ==		SystemInfo.tcUniversallyUnique:
			tag = get_id( system_info.tag_bits )
		
		elif system_info.tag_creation ==	SystemInfo.tcDatabaseID:
			tag = getTagFormatStr( system_info.tag_template ).format( n=self.id )
			
		elif system_info.tag_creation ==	SystemInfo.tcLicenseCode:
			if self.license_code:
				tag = getTagFromLicense( self.license_code, system_info.tag_from_license_id )
			else:
				tag = get_id(system_info.tag_bits)
		else:
			assert False, 'Unknown tag creation option'
		
		if validate:
			while LicenseHolder.objects.filter(existing_tag=tag).exists():
				tag = get_id( system_info.tag_bits )
		
		return tag
	
	def get_existing_tag_str( self ):
		return u', '.join( [t for t in [self.existing_tag, self.existing_tag2] if t] )
	
	def get_existing_tag_str_abbr( self ):
		def tag_abbr( tag ):
			if tag and len(tag) > 8:
				tag = tag[:8] + u'...'
			return tag
		return u', '.join( [t for t in [tag_abbr(self.existing_tag), tag_abbr(self.existing_tag2)] if t] )
	
	def get_participation_as_competitor( self ):
		return Participant.objects.select_related('competition', 'team', 'category').filter(
			license_holder=self, role=Participant.Competitor, category__isnull=False
		).order_by( '-competition__start_date' )
	
	def get_results( self, past_event_date_time_max = None ):
		results = []
		select_related = ('event', 'event__competition', 'participant', 'participant__team', 'participant__category')
		q = Q( participant__license_holder=self )
		if past_event_date_time_max:
			q &= Q( event__date_time__ge=past_event_date_time_max )
		for ResultClass in (ResultMassStart, ResultTT):
			results.extend( list(ResultClass.objects.select_related(*select_related).filter(q)) )
		results.sort( key=operator.attrgetter('event.date_time'), reverse=True )
		return results
	
	def get_tt_metric( self, ref_date ):
		years = (ref_date - self.date_of_birth).days / 365.26
		dy = years - 24.0	# Fastest estimated year.
		if dy < 0:
			dy *= 4
		return -(dy ** 2)
	
	@property
	def competition_count( self ):
		return Participant.objects.filter(license_holder=self).values_list('competition',flat=True).distinct().count()
	
	@classmethod
	def get_duplicates( cls ):
		duplicates = defaultdict( list )
		for last_name, first_name, gender, date_of_birth, uci_id, pk in LicenseHolder.objects.values_list(
				'last_name','first_name','gender','date_of_birth','uci_id','pk'):
			
			name_initial = u'{}, {}'.format(utils.removeDiacritic(last_name).upper(), utils.removeDiacritic(first_name[:1]).upper())
			key = (
				name_initial,
				gender,
				date_of_birth
			)
			duplicates[key].append( pk )
			if uci_id:
				duplicates[(u'{} UCIID'.format(u' '.join( uci_id[i:i+3] for i in range(0, len(uci_id), 3) )),None,None)].append( pk )
			
			# Check for reversed day/month
			if date_of_birth.day != date_of_birth.month and date_of_birth.day <= 12:
				key = (
					name_initial,
					gender,
					datetime.date(year=date_of_birth.year, month=date_of_birth.day, day=date_of_birth.month)
				)
				if key in duplicates:
					duplicates[key].append( pk )
			
			# Check for improper gender
			key = (
				name_initial,
				1 - gender,
				date_of_birth
			)
			if key in duplicates:
				duplicates[key].append( pk )
		
		duplicates = [{
				'key': key,
				'duplicateIds': u','.join(u'{}'.format(pk) for pk in pks),
				'license_holders': LicenseHolder.objects.filter(pk__in=pks).order_by('search_text'),
				'license_holders_len': len(pks),
			} for key, pks in duplicates.items() if len(pks) > 1]
			
		duplicates.sort( key=lambda r: r['key'] )
		return duplicates

	@classmethod
	def get_errors( cls ):
		license_holders = LicenseHolder.objects.filter(
			pk__in=Participant.objects.all().values_list('license_holder',flat=True).distinct()
		)
		return (lh for lh in license_holders if lh.has_error)
	
	@property
	def nation_title( self ):
		country = country_from_ioc(self.nation_code)
		if country:
			return u'{} - {}'.format(self.nation_code, country )
		return self.nation_code
		
	def get_uci_html( self ):
		nation_code = self.uci_country
		uci_code = self.uci_code
		return mark_safe('<imgsrc="{}/{}.png" title="{}"/>&nbsp;{}'.format(static('flags'), nation_code, self.nation_title, uci_code) ) if nation_code else uci_code
	
	def get_nation_code_html( self ):
		if self.nation_code and self.nation_code in uci_country_codes_set:
			return mark_safe('<img src="{}/{}.png" title="{}"/>&nbsp;{}'.format(static('flags'), self.nation_code, self.nation_title, self.nation_code) )
		else:
			return self.nation_code
	
	def get_uci_id_text( self ):
		return u' '.join( self.uci_id[i:i+3] for i in range(0, len(self.uci_id), 3) )
	
	def get_uci_id_html( self ):
		return mark_safe( u'&nbsp;'.join( self.uci_id[i:i+3] for i in range(0, len(self.uci_id), 3) ) )
	
	def get_flag_uci_id_html( self ):
		if self.nation_code and self.nation_code in uci_country_codes_set:
			flag = '<img src="{}/{}.png" title="{}"/>'.format(static('flags'), self.nation_code, self.nation_title)
		else:
			flag = self.nation_code
		uci_id = u'&nbsp;'.join( self.uci_id[i:i+3] for i in range(0, len(self.uci_id), 3) )
		return mark_safe( u'{}&nbsp;{}'.format(flag, uci_id) )
	
	def get_team_for_discipline( self, discipline, teamHintOnly=False ):
		team_hint = TeamHint.objects.filter(license_holder=self, discipline=discipline).order_by('-effective_date').first()
		if teamHintOnly:
			return team_hint.team if team_hint else None
		
		# Try to find a participant in this discipline.
		q_participant = Participant.objects.filter(license_holder=self,competition__discipline=discipline)
		if team_hint:
			q_participant = q_participant.filter(competition__start_date__gt=team_hint.effective_date)
		participant = q_participant.order_by('-competition__start_date').first()
		
		if not participant and not team_hint:
			# Try to find a participant in any discipline.
			q_participant = Participant.objects.filter(license_holder=self)
			if team_hint:
				q_participant = q_participant.filter(competition__start_date__gt=team_hint.effective_date)
			participant = q_participant.order_by('-competition__start_date').first()
		
		if participant:
			return participant.team
		elif team_hint:
			return team_hint.team
		return None
		
	def get_teams_for_disciplines( self, disciplines, teamHintOnly=False ):
		return [self.get_team_for_discipline(d, teamHintOnly) for d in disciplines] if disciplines else []
		
	def get_teams_for_disciplines_html( self, disciplines, teamHintOnly=False ):
		r = []
		for t in self.get_teams_for_disciplines(disciplines, teamHintOnly):
			r.append( u'<td>{}</td>'.format( escape(t.name) if t else u'Independent' ) )
		return mark_safe(''.join(r))
	
	def get_tag_str( self ):
		tags = (self.existing_tag, self.existing_tag2)
		return u'{}, {}'.format( *tags ) if (tags[0] and tags[1]) else (tags[0] or tags[1] or u'')
	
	def get_short_tag_str( self ):
		tags = (self.existing_tag, self.existing_tag2)
		tags = [t[:8] + '...' if t and len(t) > 8 else t for t in tags]
		return u'{}, {}'.format( *tags ) if (tags[0] and tags[1]) else (tags[0] or tags[1] or u'')
	
	class Meta:
		verbose_name = _('LicenseHolder')
		verbose_name_plural = _('LicenseHolders')
		ordering = ['search_text']

def add_name_to_tag( competition, tag ):
	s = [tag]
	lh = None
	bibs = []
	
	for p in Participant.objects.filter( competition=competition, tag=tag ).defer('signature'):
		if not lh:
			lh = p.license_holder
		if p.bib and p.license_holder == lh:
			bibs.append( p.bib )
			
	if not lh and competition.use_existing_tags:
		lh = LicenseHolder.objects.filter( existing_tag=tag ).first()
	
	if lh:
		s.extend( [u': ', lh.first_last] )
	if bibs:
		s.extend( [u'; ', _('Bib'), u' ', u', '.join( u'{}'.format(b) for b in bibs )] )
	return format_lazy( u'{}'*len(s), *s )
		
#---------------------------------------------------------------
class Waiver(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index=True, on_delete=models.CASCADE )
	legal_entity = models.ForeignKey( 'LegalEntity', db_index=True, on_delete=models.CASCADE )
	date_signed = models.DateField( null=True, default=None, db_index=True, verbose_name=_('Waiver Signed on') )
	
	class Meta:
		unique_together = (
			('license_holder', 'legal_entity'),
		)
		verbose_name = _('Waiver')
		verbose_name_plural = _('Waivers')

#---------------------------------------------------------------

class Result(models.Model):
	participant = models.ForeignKey( 'Participant', db_index=True, on_delete=models.CASCADE )
	# Figure out how to translate these (FIXLATER).
	cFinisher, cPUL, cOTB, cDNF, cDQ, cDNS, cNP = range(7)
	STATUS_CODE_NAMES = (
		(cFinisher, 'Finisher'),
		(cPUL,	'PUL'),	
		(cOTB,	'OTB'),
		(cDNF, 	'DNF'),
		(cDQ,	'DQ'),
		(cDNS,	'DNS'),
		(cNP,	'NP'),
	)
	STATUS_CHOICES = STATUS_CODE_NAMES
	status = models.PositiveSmallIntegerField( default=0, choices=STATUS_CHOICES, verbose_name=_('Status') )
	
	category_rank = models.PositiveSmallIntegerField( default=32000, verbose_name=_('Category Rank') )
	category_starters = models.PositiveSmallIntegerField( default=0, verbose_name=_('Category Starters') )
	category_gap = models.CharField( max_length=8, blank=True, default='' )
	
	wave_rank = models.PositiveSmallIntegerField( default=32000, verbose_name=_('Wave Rank') )
	wave_starters = models.PositiveSmallIntegerField( default=0, verbose_name=_('Wave Starters') )
	wave_gap = models.CharField( max_length=8, blank=True, default='' )
	
	finish_time = DurationField.DurationField( default=None, null=True, blank=True, verbose_name=_('Finish Time') )
	adjustment_time = DurationField.DurationField( default=None, null=True, blank=True, verbose_name=_('Adjustment Time') )
	adjustment_note = models.CharField( max_length=128, default='', blank=True, verbose_name=_('Adjustment Note') )
	
	ave_kmh = models.FloatField( default=0.0, null=True, blank=True, verbose_name=_('Ave km/h') )
	
	points = models.SmallIntegerField( default=0, verbose_name=_('Points') )
	time_bonus = DurationField.DurationField( null=True, blank=True, verbose_name=_('Time Bonus') )
	
	relegated = models.BooleanField( default=False, verbose_name=_('Relegated') )

	@property
	def adjusted_finish_time( self ):
		if self.finish_time and self.adjustment_time:
			return DurationField.formatted_timedelta(seconds=self.finish_time.total_seconds() + self.adjustment_time.total_seconds())
		return self.finish_time
	
	@property
	def status_text( self ):
		return self.STATUS_CODE_NAMES[self.status][1]
	
	def get_race_time_class( self ):
		raise NotImplementedError("Please Implement this method")
		
	def get_race_time_query( self ):
		return self.get_race_time_class().objects.filter(result=self)
	
	def format_result_html( self, rank, gap, starters ):
		if self.status == 0:
			if rank == 1:
				gap = u', winner'
			else:
				gap = u', gap:{}'.format(gap) if gap else ''
		else:
			rank = self.get_status_display()
			gap = ''
		
		return mark_safe(u'{}/{}{}'.format(rank, starters, gap).replace(' ', '&nbsp;'))
	
	@property
	def is_finisher( self ):
		return self.status in (self.cFinisher, self.cPUL)
	
	@property
	def category_result_html( self ):
		return self.format_result_html( self.category_rank, self.category_gap, self.category_starters )
	
	@property
	def wave_result_html( self ):
		return self.format_result_html( self.wave_rank, self.wave_gap, self.wave_starters )
	
	@property
	def wave_rank_html( self ):
		if self.status != 0:
			return self.get_status_display()
		return mark_safe(u'{}{}.'.format(self.wave_rank, u'&nbsp;REL' if self.relegated else u''))
	
	@property
	def category_rank_html( self ):
		if self.status != 0:
			return self.get_status_display()
		return mark_safe(u'{}{}.'.format(self.category_rank, u'&nbsp;REL' if self.relegated else u''))
	
	@property
	def result_html( self ):
		wave = self.event.get_wave_for_category( self.participant.category )
		return self.wave_result_html if wave.rank_categories_together else self.category_result_html
	
	def has_race_times( self ):
		return self.get_race_time_query().exists()
	
	def set_race_times( self, race_times, lap_speeds=[], do_create=True ):
		self.delete_race_times()
		if len(lap_speeds) < len(race_times)-1:
			lap_speeds.extend( [0.0] * (len(race_times) - 1 - len(lap_speeds) ) )
		if len(race_times) >= 2:
			RTC = self.get_race_time_class()
			rtcs = [
				RTC(
					result=self,
					race_time=DurationField.formatted_timedelta(seconds=rt),
					lap_kmh=lap_speeds[i-1] if i > 0 else 0.0,
				) for i, rt in enumerate(race_times)
			]
			if do_create:
				RTC.objects.bulk_create( rtcs )
			else:
				return rtcs
		return None
			
	def set_lap_times( self, lap_times, lap_speeds=[] ):
		race_times = [0.0]
		for lt in lap_times:
			race_times.append( race_times[-1] + lt )
		self.set_race_times( race_times, lap_speeds )
	
	def add_race_time( self, rt, lk=0.0 ):
		self.get_race_time_class()( result=self, race_time=DurationField.formatted_timedelta(seconds=rt), lap_kmh=lk ).save()
		
	def add_lap_time( self, lt, lk=0.0 ):
		rt = self.get_race_query().order_by('-race_time').first()
		rt_last = rt.race_time if rt else 0.0
		self.add_race_time( rt_last + lt, lk )
	
	def delete_race_times( self ):
		self.get_race_time_query().delete()
		
	def get_race_times( self ):
		return [ rt.total_seconds() for rt in self.get_race_time_query().values_list('race_time',flat=True) ]
		
	def get_num_laps( self ):
		return self.get_race_time_query().count() - 1
	
	def get_num_laps_fast( self ):
		try:
			return self._num_laps
		except:
			self._num_laps = self.get_num_laps()
			return self._num_laps
	
	def get_lap_kmh( self ):
		lap_kmh = []
		for lk in self.get_race_time_query().values_list('lap_kmh',flat=True)[1:]:
			if not lk:
				return []
			lap_kmh.append( lk )
		return lap_kmh
		
	def get_lap_km( self ):
		lap_km = []
		t_last = None
		for rt in self.get_race_time_query():
			t_cur = rt.race_time.total_seconds()
			if t_last is None:
				t_last = t_cur
				continue
			if not rt.lap_kmh:
				return []
			lap_km.append( rt.lap_km * (t_cur - t_last)/(60.0*60.0) )
			t_last = t_cur
		return lap_km
	
	def get_info_by_lap( self ):
		race_times = []
		lap_kmh = []
		lap_km = []
		t_last = None
		for rt in self.get_race_time_query():
			t_cur = rt.race_time.total_seconds()
			race_times.append( t_cur )
			if t_last is None:
				t_last = t_cur
				continue
			lap_kmh.append( rt.lap_kmh or 0.0 )
			lap_km.append( lap_kmh[-1] * (t_cur - t_last)/(60.0*60.0) )
				
		return {'race_times':race_times, 'lap_kmh':lap_kmh if any(lap_kmh) else None, 'lap_km':lap_km if any(lap_km) else None}
	
	def get_race_time( self, lap ):
		return self.get_race_time_query()[lap]
	
	def get_lap_times( self ):
		race_times = self.get_race_times()
		return tuple( b - a for b, a in zip(race_times[1:], race_times) )
	
	def get_lap_time( self, lap ):
		race_times = list( self.get_race_time_query()[lap-1:lap] )
		return race_times[1] - race_times[0]
	
	class Meta:
		verbose_name = _('Result')
		verbose_name_plural = _('Results')
		abstract = True
		ordering = ['status', 'wave_rank']

class ResultMassStart(Result):
	event = models.ForeignKey( 'EventMassStart', db_index=True, on_delete=models.CASCADE )
	def get_race_time_class( self ):
		return RaceTimeMassStart
		
	class Meta:
		unique_together = (
			('participant', 'event'),
		)
		verbose_name = _('ResultMassStart')
		verbose_name_plural = _('ResultsMassStart')

class ResultTT(Result):
	event = models.ForeignKey( 'EventTT', db_index=True, on_delete=models.CASCADE )
	def get_race_time_class( self ):
		return RaceTimeTT
	
	class Meta:
		unique_together = (
			('participant', 'event'),
		)
		verbose_name = _('ResultTT')
		verbose_name_plural = _('ResultsTT')

#---------------------------------------------------------------

class RaceTime(models.Model):
	race_time = DurationField.DurationField( verbose_name=_('Race Time') )
	lap_kmh = models.FloatField( blank=True, default=0.0, verbose_name=_('Lap km/h') )
	
	class Meta:
		verbose_name = _('RaceTime')
		verbose_name_plural = _('RaceTimes')
		ordering = ['race_time']
		abstract = True

class RaceTimeMassStart(RaceTime):
	result = models.ForeignKey( 'ResultMassStart', verbose_name=_('ResultMassStart'), on_delete=models.CASCADE )
	
	class Meta:
		verbose_name = _('RaceTimeMassStart')
		verbose_name_plural = _('RaceTimesMassStart')

class RaceTimeTT(RaceTime):
	result = models.ForeignKey( 'ResultTT', verbose_name=_('ResultTT'), on_delete=models.CASCADE )
	
	class Meta:
		verbose_name = _('RaceTimeTT')
		verbose_name_plural = _('RaceTimesTT')

#---------------------------------------------------------------
#---------------------------------------------------------------

def validate_str_list( r ):
	r = re.sub( r',,+', ',', r )					# Remove repeated commas.
	if r.startswith(','):
		r = r[1:]
	if r.endswith(','):
		r = r[:-1]
	return r

class CustomCategory(Sequence):
	name = models.CharField( max_length=80, verbose_name=_('Name') )
	range_str = models.CharField( default='', blank=True, max_length=128, verbose_name=_('Bib Ranges'),
		help_text = _('e.g. 1-199, -35-45') )
	nation_code_str = models.CharField( default='', blank=True, max_length=128, verbose_name=_("Nation Codes"),
		help_text = _('3-letter IOC Country Codes, comma separated') )
	GENDER_CHOICES = tuple( list(Category.GENDER_CHOICES[:-1]) + [(2,_('All'))] )
	gender = models.PositiveSmallIntegerField( choices=GENDER_CHOICES, default=2, verbose_name=_('Gender') )
	license_code_prefixes = models.CharField( default='', blank=True, max_length=32, verbose_name=_("License Code Prefixes"),
		help_text = _('e.g. "ON,BC" comma separated') )
	state_prov_str =  models.CharField( default='', blank=True, max_length=128, verbose_name=_("State/Provs"),
		help_text = _('States or Provinces, comma separated') )
	
	competitive_age_minimum = models.PositiveSmallIntegerField( default=None, null=True, blank=True,
		verbose_name=_('Competitive Age Min') )
	competitive_age_maximum = models.PositiveSmallIntegerField( default=None, null=True, blank=True,
		verbose_name=_('Competitive Age Max') )
		
	date_of_birth_minimum = models.DateField( default=None, null=True, blank=True, verbose_name=_('Born After') )
	date_of_birth_maximum = models.DateField( default=None, null=True, blank=True, verbose_name=_('Born Before') )
	
	in_category = models.ForeignKey( 'Category', blank=True, default=None, null=True, on_delete=models.SET_NULL, verbose_name=_('In Category') )
	
	def full_name( self ):
		return format_lazy( u'{}, {}', self.name, Category.GENDER_CHOICES[self.gender][1] )
	
	@property
	def code( self ):
		return self.name
	
	@property
	def code_gender( self ):
		return format_lazy(u'{} ({})', self.name, Category.GENDER_CHOICES[self.gender][1] )
	
	def validate( self ):
		self.range_str = validate_range_str( self.range_str )
		 # Replace invalid characters with commas.
		self.nation_code_str = validate_str_list( re.sub(r'[^A-Z]', ',', self.nation_code_str, flags=re.IGNORECASE) )
		self.license_code_prefixes = validate_str_list(re.sub( r'[^A-Z0-9]', ',', self.license_code_prefixes, flags=re.IGNORECASE) )
		self.state_prov_str = validate_str_list( re.sub(r'[^A-Z0-9 -.]', ',', self.state_prov_str, flags=re.IGNORECASE) )
		return self.range_str
	
	def get_participant_query( self ):
		q = Q()
		self.validate()
		if self.range_str:
			q &= get_bib_query( get_numbers(self.range_str) )
		if self.gender != 2:
			q &= Q(license_holder__gender=self.gender)
		if self.competitive_age_minimum:
			q &= Q(license_holder__date_of_birth__lte=datetime.date(self.event.date_time.year-self.competitive_age_minimum, 12, 31))
		if self.competitive_age_maximum:
			q &= Q(license_holder__date_of_birth__gte=datetime.date(self.event.date_time.year-self.competitive_age_maximum, 1, 1))
		if self.date_of_birth_minimum:
			q &= Q(license_holder__date_of_birth__gte=self.date_of_birth_minimum)
		if self.date_of_birth_maximum:
			q &= Q(license_holder__date_of_birth__lte=self.date_of_birth_maximum)
		if self.license_code_prefixes:
			q &= Q(license_holder__license_code__iregex=u'^({}).*$'.format(self.license_code_prefixes.replace(',','|')))
		if self.nation_code_str:
			q &= Q(license_holder__nation_code__iregex=u'^({})$'.format(self.nation_code_str.replace(',','|')))
		if self.state_prov_str:
			q &= Q(license_holder__state_prov__iregex=u'^({})$'.format(self.state_prov_str.replace('.',r'\.').replace(',','|')))
		if self.in_category:
			q &= Q(category=self.in_category)
		return q
	
	def get_bibs( self ):
		return self.event.get_participants().filter(self.get_participant_query()).exclude(bib__isnull=True).values_list('bib',flat=True)
	
	def make_copy( self, event_new ):
		custom_category = self
		custom_category.pk = None
		custom_category.id = None
		custom_category.event = event_new
		custom_category.save()
		return custom_category
	
	def save(self, *args, **kwargs):
		self.validate()
		return super(CustomCategory, self).save( *args, **kwargs )
		
	def has_results( self ):
		custom_participants = self.event.get_participants().filter(self.get_participant_query())
		return self.event.get_results().filter( participant__in=custom_participants ).exists()
	
	def get_results_count( self ):
		custom_participants = self.event.get_participants().filter(self.get_participant_query())
		return self.event.get_results().filter( participant__in=custom_participants ).count()
	
	def get_results( self ):
		custom_participants = self.event.get_participants().filter(self.get_participant_query())
		results_query = self.event.get_results().filter(participant__in=custom_participants)
		results = list( results_query )
			
		if not results:
			return results
		
		if getattr(self.event, 'win_and_out', False):
			results.sort( key=lambda rr: (rr.status, rr.get_num_laps(), rr.participant.bib) )
			for rr in results:
				rr.wave_gap = rr.category_gap = u''
			return results
		
		# Rank the combined results together.
		if custom_participants.values('category__id').distinct().count() == 1:
			results.sort( key=lambda rr: rr.category_rank )
		else:
			results.sort( key=lambda rr: (rr.status, -rr.get_num_laps(), rr.adjusted_finish_time, rr.wave_rank, rr.participant.bib) )
		
		winner = results[0]
		winner_time = winner.adjusted_finish_time
		if winner.status != 0 or not winner_time:
			for rr in results:
				rr.wave_gap = rr.category_gap = u''
			return results

		winner_laps = winner.get_num_laps()
		for rr in results:
			if rr is winner or rr.status != 0:
				rr.wave_gap = rr.category_gap = u''
				continue
			
			if winner_laps:
				laps_down = winner_laps - rr.get_num_laps()
				if laps_down > 0:
					rr.wave_gap = rr.category_gap = u'-{} {}'.format(laps_down, ('lap','laps')[int(laps_down>1)])
					continue
				
			rr_time = rr.adjusted_finish_time
			if not rr_time:
				rr.wave_gap = rr.category_gap = u''
				continue
				
			t = DurationField.formatted_timedelta(seconds=rr_time.total_seconds() - winner_time.total_seconds())
			rr.wave_gap = rr.category_gap = t.format_no_decimals()

		return results
	
	def get_prereg_results( self ):
		assert not self.has_results()
		
		RC = self.event.get_result_class()
		participants = self.event.get_participants().filter(self.get_participant_query())
		
		wave_starters = participants.count()
		return [
			RC(
				event=self.event,
				participant=p,
				status=Result.cNP,
				category_rank=pos, category_starters=wave_starters,
				wave_rank=pos, wave_starters=wave_starters,
			) for pos, p in enumerate(participants.order_by('license_holder__search_text'), 1) ]
	
	class Meta:
		verbose_name = _('CustomCstegory')
		verbose_name_plural = _('CustomCategories')
		abstract = True

class CustomCategoryMassStart(CustomCategory):
	event = models.ForeignKey( 'EventMassStart', verbose_name=_('EventMassSart'), on_delete=models.CASCADE )
	
	def get_container( self ):
		return self.event.customcategorymassstart_set.all()
	
	class Meta:
		verbose_name = _('CustomCategoryMassStart')
		verbose_name_plural = _('CustomCategoriesMassStart')

class CustomCategoryTT(CustomCategory):
	event = models.ForeignKey( 'EventTT', verbose_name=_('EventTT'), on_delete=models.CASCADE )
	
	def get_container( self ):
		return self.event.customcategorytt_set.all()
	
	class Meta:
		verbose_name = _('CustomCategoryTT')
		verbose_name_plural = _('CustomCategoriesTT')
		
#---------------------------------------------------------------
#---------------------------------------------------------------

class TeamHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True, on_delete=models.CASCADE )
	discipline = models.ForeignKey( 'Discipline', db_index = True, on_delete=models.CASCADE )
	team = models.ForeignKey( 'Team', db_index=True, null=True, on_delete=models.CASCADE )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def __str__( self ):
		return u', '.join((u'{}'.format(self.license_holder), u'{}'.format(self.discipline), u'{}'.format(self.team), u'{}'.format(self.effective_date)))
	
	def __repr__( self ):
		return u'TeamHint({})'.format(self.__str__())

	@staticmethod
	def set_all_disciplines( license_holder, team ):
		TeamHint.objects.filter(license_holder=license_holder, team=team).delete()
		effective_date = timezone.localtime(timezone.now()).date()
		TeamHint.objects.bulk_create( 
			[TeamHint(license_holder=license_holder, discipline=discipline, team=team, effective_date=effective_date)
				for discipline in Discipline.objects.all()]
		)
		
	@staticmethod
	def set_discipline( license_holder, discipline, team ):
		th = TeamHint.objects.filter(license_holder=license_holder, discipline=discipline).order_by('-effective_date').first()
		effective_date = timezone.localtime(timezone.now()).date()
		if th:
			TeamHint.objects.filter( license_holder=license_holder, discipline=discipline ).exclude( pk=th.pk ).delete()
			th.team = team
			th.effective_date=effective_date
		else:
			th = TeamHint( license_holder=license_holder, discipline=discipline, effective_date=effective_date )
		th.save()
		
	class Meta:
		verbose_name = _('TeamHint')
		verbose_name_plural = _('TeamHints')

def update_team_hints():
	latest_competition_date = timezone.localtime(timezone.now()).date() - datetime.timedelta( days=365*2 )
	most_recent = {}
	
	# Add all the known TeamHints.
	for license_holder, discipline, team, effective_date in TeamHint.objects.all().values_list(
			'license_holder','discipline','team','effective_date').order_by( '-effective_date' ):
		key = (license_holder, discipline)
		if key not in most_recent:
			most_recent[key] = (effective_date, team)
			
	# Then update with all known teams (includes None for Independent).
	for license_holder, discipline, team, effective_date in Participant.objects.filter(
				competition__start_date__gte=latest_competition_date).values_list(
				'license_holder', 'competition__discipline', 'team', 'competition__start_date').order_by('-competition__start_date'):
		key = (license_holder, discipline)
		if key not in most_recent or effective_date > most_recent[key][0]:
			most_recent[key] = (effective_date, team)
	
	# Update the TeamHints with the latest team information by discipline.
	TeamHint.objects.all().delete()
	with BulkSave() as b:
		for (license_holder, discipline), (effective_date, team) in most_recent.items():
			th = TeamHint()
			th.license_holder_id = license_holder
			th.discipline_id = discipline
			th.team_id = team
			th.effective_date = effective_date
			b.append( th )

class CategoryHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True, on_delete=models.CASCADE )
	discipline = models.ForeignKey( 'Discipline', db_index = True, on_delete=models.CASCADE )
	category = models.ForeignKey( 'Category', db_index = True, on_delete=models.CASCADE )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def __str__( self ):
		return u'{}'.format(self.license_holder) + ' ' + u'{}'.format(self.discipline) + ' ' + u'{}'.format(self.category) + ' ' + u'{}'.format(self.effective_date)
	
	class Meta:
		verbose_name = _('CategoryHint')
		verbose_name_plural = _('CategoryHints')

def update_category_hints():
	latest_competition_date = timezone.localtime(timezone.now()).date() - datetime.timedelta( days=365*2 )
	most_recent = {}
	
	# Add all the known CategoryHints.
	for license_holder, discipline, category_format, category, effective_date in CategoryHint.objects.all().values_list(
			'license_holder','discipline','category__format','category','effective_date').order_by( '-effective_date' ):
		key = (license_holder, discipline, category_format)
		if key not in most_recent:
			most_recent[key] = (effective_date, category)
			
	# Then update with all known categories.
	for license_holder, discipline, category_format, category, effective_date in Participant.objects.filter(
				category__isnull=False, competition__start_date__gte=latest_competition_date).values_list(
				'license_holder', 'competition__discipline','category__format', 'category', 'competition__start_date').order_by('-competition__start_date'):
		key = (license_holder, discipline, category_format)
		if key not in most_recent or effective_date > most_recent[key][0]:
			most_recent[key] = (effective_date, category)
	
	# Update the CategoryHints with the latest category information by discipline.
	CategoryHint.objects.all().delete()
	with BulkSave() as b:
		for (license_holder, category_format, discipline), (effective_date, category) in most_recent.items():
			ch = CategoryHint()
			ch.license_holder_id = license_holder
			ch.discipline_id = discipline
			ch.category_id = category
			ch.effective_date = effective_date
			b.append( ch )

class NumberSetEntry(models.Model):
	number_set = models.ForeignKey( 'NumberSet', db_index = True, on_delete=models.CASCADE )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True, on_delete=models.CASCADE )
	bib = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Bib') )
	date_issued = models.DateField( db_index=True, null=True, default=None, verbose_name=_('Date Issued') )
	
	# If date_lost is null, the number is in use.
	date_lost = models.DateField( db_index=True, null=True, default=None, verbose_name=_('Date Lost') )
	
	def save( self ):
		if self.date_lost is None and self.id is None and self.number_set.get_bib_available(self.bib) <= 0:
			raise IntegrityError()
		if self.date_issued is None:
			self.date_issued = datetime.date.today()
		return super( NumberSetEntry, self ).save()
	
	class Meta:
		verbose_name = _('NumberSetEntry')
		verbose_name_plural = _('NumberSetEntries')
		
class FormatTimeDelta( datetime.timedelta ):
	def __repr__( self ):
		fraction, seconds = math.modf( self.total_seconds() )
		seconds = int(seconds)
		return '{}:{:02d}:{:02.3f}'.format(seconds // (60*60), (seconds // 60) % 60, seconds % 60 + fraction)
	
	def __str__( self ):
		return u'{}'.format( self.__repr__() )

class ParticipantDefaultValues( object ):
	def __init__( self, competition ):
		self.competition = competition
		self.category_format = self.competition.category_format
		self.category_init_date = datetime.date(1920,1,1)
		self.category = None
		self.team_init_date = datetime.date(1920,1,1)
		self.team = None
		self.role_init_date = datetime.date(1920,1,1)
		self.role = None
		self.est_kmh_init_date = datetime.date(1920,1,1)
		self.est_kmh = None
		
	def done( self ):
		return self.team and self.role and self.category
		
	def update_participant( self, pp ):
		if not pp:
			return
			
		if not self.est_kmh and pp.est_kmh:
			self.est_kmh = pp.est_kmh
		
		if pp.competition.start_date > self.category_init_date and pp.category and pp.competition.category_format == self.competition.category_format:
			self.category = pp.category
			self.category_init_date = pp.competition.start_date
		
		if pp.competition.start_date > self.team_init_date:
			self.team = pp.team
			self.team_init_date = pp.competition.start_date
		
		if pp.competition.start_date > self.role_init_date:
			self.role = pp.role
			self.role_init_date = pp.competition.start_date
		
		return self.done()

	def update_team_hint( self, th ):
		if th and th.effective_date > self.team_init_date:
			self.team = th.team
			self.team_init_date = th.effective_date
		return self.done()
			
	def update_category_hint( self, ch ):
		if ch and ch.category.format == self.category_format and ch.effective_date > self.category_init_date:
			self.category = ch.category
			self.category_init_date = ch.effective_date
		return self.done()
		
	def update_results_avg_kmh( self, license_holder ):
		ave_kmh = sorted( ResultTT.objects.filter(
			status=Result.cFinisher,
			participant__license_holder=license_holder,
			event__competition__discipline=self.competition.discipline,
			ave_kmh__isnull=False,
			).exclude( ave_kmh__lte=0.0,
			).order_by('-event__date_time',
			)[:3].values_list( 'ave_kmh', flat=True )
		)
		if ave_kmh:
			lak = len(ave_kmh)
			if lak & 1:
				self.est_kmh = ave_kmh[lak//2]
			else:
				m = lak // 2
				self.est_kmh = (ave_kmh[m-1] + ave_kmh[m]) / 2.0
		
class Participant(models.Model):
	competition = models.ForeignKey( 'Competition', db_index=True, on_delete=models.CASCADE )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index=True, on_delete=models.CASCADE )
	team = models.ForeignKey( 'Team', null=True, db_index=True, on_delete=models.SET_NULL )
	
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
	category=models.ForeignKey( 'Category', null=True, blank=True, db_index=True, on_delete=models.SET_NULL )
	
	bib=models.PositiveSmallIntegerField( null=True, blank=True, db_index=True, verbose_name=_('Bib') )
	
	tag=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag') )
	tag2=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag2') )
	tag_checked=models.BooleanField( default=False, verbose_name=_('Tag Checked') )

	license_checked=models.BooleanField( default=False, verbose_name=_('License Checked') )
	signature=models.TextField( blank=True, default='', verbose_name=_('Signature') )
	
	@property
	def is_jsignature( self ):
		return self.signature and self.signature.startswith('image/svg+xml;base64')

	paid=models.BooleanField( default=False, verbose_name=_('Paid') )
	confirmed=models.BooleanField( default=False, verbose_name=_('Confirmed') )
	
	note=models.TextField( blank=True, default='', verbose_name=_('Note') )
	
	est_kmh=models.FloatField( default=0.0, verbose_name=_('Est Kmh') )
	seed_early=models.BooleanField( default=False, verbose_name=_('Seed Early') )
	SEED_OPTION_CHOICES = ((1,_('-')),(0,_('Seed Early')),(2,_('Seed Late')),(3,_('Seed Last')),)
	seed_option=models.SmallIntegerField( choices=SEED_OPTION_CHOICES, default=1, verbose_name=_('Seed Option') )
	
	def is_license_check_required( self ):
		return CompetitionCategoryOption.is_license_check_required(self.competition, self.category)
	
	def is_license_checked( self ):
		# Check trival cases.
		if (	self.license_checked or
				not self.competition.report_label_license_check or
				not self.is_license_check_required()
			):
			return True			
		return LicenseCheckState.check_participant( self )
	
	def enforce_tag_constraints( self ):
		license_holder = self.license_holder
		competition = self.competition
		
		# Enforce tag conistency with license holder.
		if competition.using_tags and competition.use_existing_tags and (
					self.tag  != license_holder.existing_tag or
					self.tag2 != license_holder.existing_tag2 ):
			self.tag  = license_holder.existing_tag
			self.tag2 = license_holder.existing_tag2
			self.save()
		return self
	
	@property
	def est_speed_display( self ):
		return u'{:g} {}{}'.format(
			self.competition.to_local_speed(self.est_kmh),
			self.competition.speed_unit_display,
			u' ({})'.format( self.get_seed_option_display() ) if self.seed_option != 1 else u'',
		)
		
	@property
	def adjusted_est_kmh( self ):
		return [-1000000.0, 0.0, 1000000, 10000000][self.seed_option] + self.est_kmh
	
	def get_tt_km( self ):
		if not self.category or not self.is_competitor:
			return None
		# Get the TT event after the current time, or the last TT event in the Competition.
		waveTTs = list(WaveTT.objects.filter(event__competition=self.competition, categories=self.category).select_related('event').order_by('event__date_time'))
		if not waveTTs:
			waveTT = None
		elif len(waveTTs) == 1:
			waveTT = waveTTs[0]
		else:
			tNow = timezone.now()
			waveTT = None
			for w in waveTTs:
				if w.event.date_time >= tNow:
					waveTT = w
			if not waveTT:
				waveTT = waveTTs[-1]
		
		if not waveTT or not waveTT.distance:
			return None
		return waveTT.distance * (waveTT.laps or 1)
	
	def get_tt_distance_text( self ):
		tt_km = self.get_tt_km()
		if not tt_km:
			return u''
		return u'{:.2f}{}'.format( self.competition.to_local_distance(tt_km), self.competition.get_distance_unit_display() )
	
	def get_tt_est_duration( self ):
		if not self.est_kmh:
			return None
		tt_km = self.get_tt_km()
		if not tt_km:
			return None
		return DurationField.formatted_timedelta( hours = tt_km / self.est_kmh )
	
	def get_tt_est_time_text( self ):
		tt_est_duration = self.get_tt_est_duration()
		if not tt_est_duration:
			return u''
		return DurationField.format_seconds( round(tt_est_duration.total_seconds()), False )
	
	@property
	def team_name( self ):
		return self.team.name if self.team else _('Independent')
	
	@property
	def category_name( self ):
		return self.category.code_gender if self.category else u''
	
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
					if not competition.number_set.assign_bib( license_holder, self.bib ):
						self.bib = None
				
			if license_holder_update:
				if competition.use_existing_tags:
					if license_holder.existing_tag != self.tag or license_holder.existing_tag2 != self.tag2:
						if self.tag:
							for license_holder_dup in list(LicenseHolder.objects.filter(existing_tag=self.tag)):
								license_holder_dup.existing_tag = license_holder_dup.get_unique_tag()
								license_holder_dup.save()
						
						if self.tag2:
							for license_holder_dup in list(LicenseHolder.objects.filter(existing_tag=self.tag2)):
								license_holder_dup.existing_tag2 = license_holder_dup.get_unique_tag()
								license_holder_dup.save()
						
						license_holder.existing_tag  = self.tag
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
		return (
			self.competition.seasons_pass and
			SeasonsPassHolder.objects.filter(seasons_pass=self.competition.seasons_pass, license_holder=self.license_holder).exists()
		)

	@property
	def role_full_name( self ):
		return u'{} {}'.format( self.ROLE_NAMES[self.roleCode], self.get_role_display() )
	
	@property
	def needs_bib( self ):
		return self.is_competitor and not self.bib
	
	@property
	def tag_valid( self ):
		competition = self.competition
		if not competition.using_tags or not self.is_competitor:
			return True
		tag = self.license_holder.existing_tag if competition.use_existing_tags else self.tag
		if competition.do_tag_validation:
			return tag and self.tag_checked
		else:
			return bool(tag)
	
	@property
	def name( self ):
		fields = [ getattr(self.license_holder, a) for a in ('first_name', 'last_name', 'uci_code', 'license_code') ]
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
	
	def sign_waiver_now( self, backdate = None ):
		legal_entity = self.competition.legal_entity
		if not legal_entity:
			return
		
		date_signed = (backdate or timezone.localtime(timezone.now()).date())
		waiver = Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).first()
		if waiver:
			if waiver.date_signed == date_signed:
				return
			waiver.date_signed = date_signed
		else:
			waiver = Waiver(
				license_holder=self.license_holder,
				legal_entity=legal_entity,
				date_signed=date_signed
			)
		waiver.save()
	
	def unsign_waiver_now( self ):
		legal_entity = self.competition.legal_entity
		if legal_entity:
			Waiver.objects.filter(license_holder=self.license_holder, legal_entity=legal_entity).delete()
	
	def __str__( self ):
		return self.name
	
	def add_to_default_optional_events( self ):
		ParticipantOption.set_option_ids(
			self,
			set( event.option_id for event in self.competition.get_events() if event.select_by_default and event.could_participate(self) )
				if self.category else []
		)
	
	def add_other_categories( self ):
		# Add participants if this license holder participanted in other categories in this race format.
		if self.role != Participant.Competitor or self.category is None:
			return
			
		# Collect a list of all categories for this participant from hints.
		categories_from_hint = list( CategoryHint.objects.filter(
				license_holder=self.license_holder,
				discipline=self.competition.discipline,
				category__format=self.competition.category_format,
			).values_list( 'category__id', 'effective_date' )
		)
		effective_date_max = max( c[1] for c in categories_from_hint ) if categories_from_hint else datetime.date.min
		
		# Find the most recent past competition for this license holder.
		previous = Participant.objects.filter(
			license_holder=self.license_holder,
			competition__discipline=self.competition.discipline,
			competition__category_format=self.competition.category_format,
			role=Participant.Competitor,
			bib__isnull=False,
			competition__start_date__lt=self.competition.start_date,
		).exclude(category__isnull=True, competition=self.competition).defer('signature').select_related('competition').order_by(
			'-competition__start_date',
		).first()
		
		if previous and previous.competition.start_date > effective_date_max:
			# Get all other categories represented by this license holder at the previous event.
			other_categories_previous = list(
				Participant.objects.filter(
					license_holder=self.license_holder,
					competition=previous.competition,
					role=Participant.Competitor,
					bib__isnull=False,
				).exclude(category__isnull=True, category=self.category).defer('signature').values_list('category__id',flat=True)
			)
		else:
			# Add corresponding participants from the hints.
			other_categories_previous = [c[0] for c in categories_from_hint]
		
		if other_categories_previous:
			for category in Category.objects.filter( id__in=other_categories_previous ):
				self.category = category
				self.bib = self.competition.number_set.get_bib( self.competition, self.license_holder, self.category ) if self.competition.number_set else None
				self.id = None
				self.pk = None
				try:
					self.save()
				except IntegrityError as e:
					# Integrity error is expected if this participant is already added.
					continue
				self.add_to_default_optional_events()
	
	def get_waves_on_standby( self ):
		if not self.category:
			return []
		q = Q(event__competition=self.competition, max_participants__is_null=False, max_participants__gt=0, categories=self.category)
		waves = (
			[w for w in Wave.objects.filter(q) if w.is_participating(self)] +
			[w for w in WaveTT.objects.filter(q) if w.is_participating(self)]
		)
		return [w for w in waves if w.get_participant_count() > w.max_participants]
	
	def init_default_values( self ):
		pdv = ParticipantDefaultValues( self.competition )
	
		self.role = 0
		
		# Unconditionally get the team based on the hint.
		if (pdv.role or 0) < 200:
			pdv.update_team_hint( TeamHint.objects.filter(license_holder=self.license_holder, discipline=self.competition.discipline).order_by(
				'-effective_date').first()
			)
		
		# Initialize from past participants of the same discipline and category_format.
		for pp in Participant.objects.filter(
					license_holder=self.license_holder,
					competition__discipline=self.competition.discipline,
					competition__category_format=self.competition.category_format,
					role=Participant.Competitor,
				).exclude(category__isnull=True).defer('signature').select_related('competition').order_by(
					'-competition__start_date','category__sequence')[:8]:
			if pdv.update_participant( pp ):
				break

		# Initialize from past participants of the same discipline (relax category format).
		if not pdv.done():
			for pp in Participant.objects.filter(
						license_holder=self.license_holder,
						competition__discipline=self.competition.discipline,
						role=Participant.Competitor,
					).exclude(category__isnull=True).defer('signature').select_related('competition').order_by(
						'-competition__start_date','category__sequence')[:8]:
				if pdv.update_participant( pp ):
					break			
				
		# Initialize from past participants of any discipline, category format or role.
		if not pdv.done():
			for pp in Participant.objects.filter(
						license_holder=self.license_holder,
						competition__discipline=self.competition.discipline,
					).exclude(category__isnull=True).defer('signature').select_related('competition').order_by(
						'-competition__start_date','category__sequence')[:8]:
				if pdv.update_participant( pp ):
					break			
		
		if not pdv.category and pdv.role == self.Competitor:
			pdv.update_category_hint( CategoryHint.objects.filter(
				license_holder=self.license_holder, discipline=self.competition.discipline, category__format=self.competition.category_format
				).order_by('-effective_date').first()
			)
		
		# If there are time trial events, initialize from past time trials results.
		if EventTT.objects.filter( competition=self.competition ).exists():
			pdv.update_results_avg_kmh( self.license_holder )
		
		self.category	= pdv.category
		self.team		= pdv.team
		self.role		= pdv.role or self.Competitor
		self.est_kmh	= pdv.est_kmh or 0.0
		
		# If we have a category, check the bib number.
		if self.category:
			cn = self.competition.get_category_numbers( self.category )
			category_numbers_set = cn.get_numbers() if cn else set()
			
			if self.bib in category_numbers_set:
				# This is a valid bib.
				if self.competition.number_set:
					self.competition.number_set.assign_bib( self.license_holder, self.bib )
			else:
				# This is an INVALID bib.
				if self.competition.number_set:
					self.bib = self.competition.number_set.get_bib( self.competition, self.license_holder, self.category, category_numbers_set )
				else:
					self.bib = None
		
		# Use default tags.
		if self.competition.use_existing_tags:
			self.tag  = self.license_holder.existing_tag
			self.tag2 = self.license_holder.existing_tag2
				
		if self.is_seasons_pass_holder:
			self.paid = True
		
		# Remove anomylous fields if not competitor.
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
	def good_license_check( self ):	return self.is_license_checked()
	def good_tag( self ):			return self.tag_valid
	def good_team( self ):			return self.is_competitor and self.team
	def good_paid( self ):			return self.is_competitor and self.paid
	def good_signature( self ):		return self.signature or (not self.competition.show_signature)
	def good_est_kmh( self ):		return self.est_kmh or not self.has_tt_events()
	def good_waiver( self ):		return not self.has_unsigned_waiver
	def good_eligible( self ):		return not self.is_competitor or self.license_holder.is_eligible
	
	def can_start( self ):
		return (
			self.good_eligible() and
			self.good_waiver() and
			self.good_paid() and
			self.good_category() and
			self.good_license_check() and
			self.good_bib() and
			self.good_tag() and
			self.good_signature()
		)
		
	@classmethod
	def get_can_start_query( cls, competition ):
		q_ineligible = Q(license_holder__eligible=False) & (Q(license_holder__ineligible_on_date_time__isnull=True) | Q(license_holder__ineligible_on_date_time__ge=timezone.now()))
		q = Q(
			role=Participant.Competitor,
			bib__isnull=False,
			category__isnull=False,
			paid=True,
		) & ~q_ineligible
		
		if competition.using_tags:
			q &= Q( tag__isnull=False )
		if competition.show_signature:
			q &= ~Q( signature='' )
		return q
		
	def can_tt_start( self ):
		return (
			self.good_eligible() and
			self.good_category()
		)
	
	@property
	def show_confirm( self ):
		return (
			self.is_competitor and
			self.good_eligible() and
			self.good_bib() and
			self.good_category() and
			self.good_license_check() and
			self.good_paid() and
			self.good_waiver()
		)
	
	@property
	def is_done( self ):
		if self.is_competitor:
			return (
				self.can_start() and
				self.good_license() and
				self.good_emergency_contact() and
				self.good_est_kmh()
			)
		elif self.role < 200:
			return (
				self.team
			)
		else:
			return True
	
	def get_lh_errors_warnings( self ):
		license_holder_errors = (
			('good_eligible',		_('Ineligible to Compete')),
			('good_waiver',			_('Missing/Expired Insurance Waiver')),
		)
		license_holder_warnings = (
			('good_license',			_('Temporary License (do you have a permanent one now?)')),
			('good_emergency_contact',	_('Incomplete Emergency Contact')),
		)
		
		return (
			[message for check, message in license_holder_errors if not getattr(self, check)()],
			[message for check, message in license_holder_warnings if not getattr(self, check)()],
		)
	
	def get_errors_warnings( self ):
		participant_errors = (
			('good_paid',			_('Missing Payment')),
			('good_bib',			_('Missing Bib Number')),
			('good_category',		_('Missing Category')),
			('good_license_check',	_('Unchecked License')),
			('good_tag',			_('Unchecked Tag')),
			('good_signature',		_('Missing Signature')),
		)
		participant_warnings = (
			#('good_team',			_('No Team Name on File')),
			('good_est_kmh',		_('Missing Estimated TT Speed')),
		)
		
		errors = []
		for check, message in participant_errors:
			if not getattr(self, check)():
				if check in ('good_bib', 'good_paid'):
					errors.append(
						format_lazy( u'{} ({})', message, self.category.code if self.category else _('Missing Category') )
					)
				else:
					errors.append( message )
		
		return errors, [message for check, message in participant_warnings if not getattr(self, check)()]
	
	def get_errors_warnings_all_categories( self ):
		errors, warnings = [], []
		for p in self.get_category_participants():
			e, w = p.get_errors_warnings()
			errors.extend( e )
			warnings.extend( w )
		return errors, warnings
		
	def get_errors_warnings_bool_all_categories( self ):
		errors_lh, warnings_lh = self.get_lh_errors_warnings()
		errors, warnings = self.get_errors_warnings_all_categories()
		return (errors_lh or errors), (warnings_lh or warnings)
	
	@property
	def is_done_for_all_categories( self ):
		return all( p.is_done for p in self.get_category_participants() )
		
	def auto_confirm( self ):
		if self.competition.start_date <= timezone.localtime(timezone.now()).date() <= self.competition.finish_date and self.show_confirm:
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
		
		category_numbers = self.competition.get_category_numbers( self.category )
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
		
		if compatible_participant and compatible_participant.bib in category_numbers.get_numbers():
			self.bib = compatible_participant.bib
		else:
			self.bib = None
	
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
		return list( conflicts.exclude(pk=self.pk) )
	
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
		waves = sorted(
			WaveTT.objects.filter(event__competition=self.competition, categories=self.category),
			key=operator.attrgetter('sequence')
		)
		waves = [w for w in waves if w.is_participating(self)]
		reg_closure_minutes = SystemInfo.get_reg_closure_minutes()
		for w in waves:
			w.is_late = w.reg_is_late( reg_closure_minutes, self.registration_timestamp )
			ett = EntryTT.objects.filter( event=w.event, participant=self ).first()
			w.clock_time = w.event.date_time + ett.start_time if ett else None
		return waves
	
	def has_start_wave_tts( self ):
		if not self.category:
			return False
		return any( w.is_participating(self) for w in
			WaveTT.objects.filter(event__competition=self.competition, categories=self.category)
		)
	
	def get_participant_events( self ):
		return self.competition.get_participant_events( self )
		
	def has_optional_events( self ):
		return any( optional for event, optional, entered in self.get_participant_events() )
	
	def has_tt_events( self ):
		return any( entered for event, optional, entered in self.get_participant_events() if event.event_type == 1 )
	
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
		tags = (self.license_holder.existing_tag, self.license_holder.existing_tag2) if self.competition.use_existing_tags else (self.tag, self.tag2)
		return u'{}, {}'.format( *tags ) if (tags[0] and tags[1]) else (tags[0] or tags[1] or u'')
	
	def get_tag( self ):
		return self.license_holder.existing_tag if self.competition.use_existing_tags else self.tag
		
	def set_tag( self, tag ):
		self.tag = tag
		if self.competition.use_existing_tags:
			self.license_holder.existing_tag = tag
			self.license_holder.save()
		self.save()
	
	def get_short_tag_str( self ):
		tags = (self.license_holder.existing_tag, self.license_holder.existing_tag2) if self.competition.use_existing_tags else (self.tag, self.tag2)
		tags = [t[:8] + '...' if t and len(t) > 8 else t for t in tags]
		return u'{}, {}'.format( *tags ) if (tags[0] and tags[1]) else (tags[0] or tags[1] or u'')
	
	def set_tag_checked( self, checked=True ):
		checked = bool( checked )
		if self.tag_checked != checked:
			self.tag_checked = checked
			self.save()
	
	def get_available_numbers( self ):
		if not self.category:
			return [], {}, [], False
			
		competition      = self.competition
		category         = self.category
		number_set       = competition.number_set
		category_numbers = competition.get_category_numbers( category )
		
		if category_numbers:
			available_numbers = sorted( category_numbers.get_numbers() )
			bib_query = category_numbers.get_bib_query()
			category_numbers_defined = True
		else:
			available_numbers = []
			bib_query = None
			category_numbers_defined = False
		
		allocated_numbers = {}
		lost_bibs = {}
		
		# Find available category numbers.
		
		# First, add all numbers allocated to this event (includes pre-reg).
		if available_numbers:
			participants = Participant.objects.filter( competition=competition ).defer( 'signature' )
			participants = participants.filter( category__in=category_numbers.categories.all() ).filter( bib_query ).order_by()
			participants = participants.select_related('license_holder')
			allocated_numbers = { p.bib: p.license_holder for p in participants }
		
		# If there is a NumberSet, add allocated numbers from there.
		if number_set and available_numbers:
			# Exclude available numbers not allowed in the number set.
			range_events = number_set.get_range_events()
			available_numbers = [bib for bib in available_numbers if number_set.is_bib_valid(bib, range_events)]
			
			# Exclude existing bib numbers of all license holders if using existing bibs.
			# For duplicate license holders, check whether the duplicate has ever raced this category before.
			# We don't know if the existing license holders will show up.
			
			bib_max = number_set.get_bib_max_count_all()
			bib_available_all = number_set.get_bib_available_all( bib_query )
			
			# Get all the bibs of license holders that match the category_numbers of this category.
			current_bibs = defaultdict( set )
			nses = number_set.numbersetentry_set.filter( date_lost__isnull=True ).filter( bib_query )
			nses = nses.select_related('license_holder')
			for nse in nses:
				current_bibs[nse.license_holder].add( nse.bib )
			
			# Handle the case of only one bib in the number set.
			for lh, bibs in current_bibs.items():
				if len(bibs) == 1:
					bib = next(iter(bibs))
					if bib_max.get(bib, 0) == 1:
						allocated_numbers[bib] = lh
						
			# Otherwise, scan past participants to check if a license holder in this category owns the bib.
			pprevious = Participant.objects.filter( competition__number_set=number_set, category__in=category_numbers.categories.all() )
			pprevious = pprevious.filter( bib_query ).defer( 'signature' )
			pprevious = pprevious.exclude( bib__in=list(allocated_numbers.keys())[:200] )
			pprevious = pprevious.order_by('-competition__start_date')
			
			for p in pprevious.exclude(license_holder=self.license_holder).select_related('license_holder'):
				if p.bib not in allocated_numbers and p.bib in current_bibs[p.license_holder]:
					allocated_numbers[p.bib] = p.license_holder
			
			nses = number_set.numbersetentry_set.exclude( date_lost__isnull=True ).filter( bib_query )
			lost_bibs = { bib:date_lost
				for bib, date_lost in nses.order_by('date_lost').values_list('bib','date_lost')
					if bib_available_all.get(bib,-1) == 0
			}
		else:
			lost_bibs = {}
			
		return available_numbers, allocated_numbers, lost_bibs, category_numbers_defined

	def get_bib_auto( self ):
		if self.bib:
			return self.bib
		available_numbers, allocated_numbers, lost_bibs, category_numbers_defined = self.get_available_numbers()
		for bib in available_numbers:
			if bib not in allocated_numbers and bib not in lost_bibs:
				return bib
		return None
	
	@staticmethod
	def most_recent():
		participants = Participant.objects.all()
		mr_team_q = participants.exclude(team__isnull=True).values_list('license_holder','competition__discipline','team').annotate(Max('competition__start_date'))
		mr_team = {}
		for lh, disc, team, dt in mr_team_q:
			key = (lh, disc)
			if key not in mr_team or mr_team[key][1] < dt:
				mr_team[key] = (team, dt)
		mr_category_q = participants.exclude(category__isnull=True).values_list('license_holder','competition__discipline','category').annotate(Max('competition__start_date'))
		mr_category = {}
		for lh, disc, cat, dt in mr_category_q:
			key = (lh, disc)
			if key not in mr_category or mr_category[key][1] < dt:
				mr_category[key] = (cat, dt)
	
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
	event = models.ForeignKey( 'EventTT', db_index = True, verbose_name=_('Event'), on_delete=models.CASCADE )
	participant = models.ForeignKey( 'Participant', db_index = True, verbose_name=_('Participant'), on_delete=models.CASCADE )
	
	est_speed = models.FloatField( default=0.0, verbose_name=_('Est. Speed') )
	hint_sequence = models.PositiveIntegerField( default=0, verbose_name = _('Hint Sequence') )
	
	start_sequence = models.PositiveIntegerField( default = 0, db_index = True, verbose_name = _('Start Sequence') )
	
	start_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Start Time') )
	
	finish_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Finish Time') )
	adjustment_time = DurationField.DurationField( null = True, blank = True, verbose_name=_('Adjustment Time') )
	adjustment_note = models.CharField( max_length = 128, default = '', verbose_name=_('Adjustment Note') )
	
	def swap_position( self, tt ):
		self.start_sequence, tt.start_sequence = tt.start_sequence, self.start_sequence
		self.start_time, tt.start_time = tt.start_time, self.start_time
	
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
		
	def get_result_class( self ):
		return ResultTT
		
	def get_race_time_class( self ):
		return RaceTimeTT
	
	def get_custom_category_class( self ):
		return CustomCategoryTT
		
	create_seeded_startlist = models.BooleanField( default=True, verbose_name=_('Create Seeded Startlist'),
		help_text=_('If True, seeded start times will be generated in the startlist for CrossMgr.  If False, no seeded times will be generated, and the TT time will start on the first recorded time in CrossMgr.') )

	group_size = models.PositiveSmallIntegerField( default=0, verbose_name = _('Group Size'),
		help_text=_('Maximum number of starters without a Group Size Gap.  The Group Size Gap will be inserted between riders of Group Size (if non-zero).') )
	group_size_gap = DurationField.DurationField( verbose_name=_('Group Size Gap'), default = duration_field_5m )
	
	def create_initial_seeding( self ):
		large_delete_all( EntryTT, Q(event=self) )
		
		min_gap = datetime.timedelta( seconds=10 )
		zero_gap = datetime.timedelta( seconds=0 )
		
		empty_gap_before_wave = zero_gap
		
		sequenceCur = 1
		groupCount = 0
		tCur = datetime.timedelta( seconds = 0 )
		for wave_tt in self.wavett_set.all():
			
			gap_before_wave = wave_tt.gap_before_wave or zero_gap
			regular_start_gap = wave_tt.regular_start_gap or zero_gap
			fastest_participants_start_gap = wave_tt.fastest_participants_start_gap or zero_gap

			participants = sorted(
				[p for p in wave_tt.get_participants_unsorted()
					.select_related('license_holder','category') if p.can_tt_start()
				],
				key=wave_tt.get_sequence_key() )
			
			# Carry the "before gaps" of empty waves.
			if not participants:
				empty_gap_before_wave = max( empty_gap_before_wave, gap_before_wave or zero_gap )
				continue
			
			last_fastest = len(participants) - wave_tt.num_fastest_participants
			entry_tt_pending = []
			for i, p in enumerate(participants):
				rider_gap = max(
					fastest_participants_start_gap if i >= last_fastest else zero_gap,
					regular_start_gap,
					min_gap,
				)
				gap = max( max(empty_gap_before_wave, gap_before_wave) if i == 0 else zero_gap, rider_gap )
				if self.group_size:
					if gap >= self.group_size_gap:
						groupCount = 0		# If there was already a gap larger than the group size gap, reset the group count.
					elif groupCount >= self.group_size:	# Else, if we are at a group boundary, insert the group gap.
						gap = max( gap, self.group_size_gap )
						groupCount = 0
					groupCount += 1
				
				tCur += gap
				
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
	event = models.ForeignKey( EventTT, db_index = True, on_delete=models.CASCADE )
	
	sequence = models.PositiveSmallIntegerField( default=0, verbose_name = _('Sequence') )
	
	# Fields for assigning start times.	
	gap_before_wave = DurationField.DurationField( null=True, blank=True, verbose_name=_('Gap Before Wave'), default = duration_field_5m )
	regular_start_gap = DurationField.DurationField( null=True, blank=True, verbose_name=_('Regular Start Gap'), default = duration_field_1m )
	fastest_participants_start_gap = DurationField.DurationField( null=True, blank=True, verbose_name=_('Fastest Participants Start Gap'), default = duration_field_2m )
	num_fastest_participants = models.PositiveSmallIntegerField(
						verbose_name=_('Number of Fastest Participants'),
						choices=[(i, '%d' % i) for i in range(0, 16)],
						help_text = 'Participants to get the Fastest gap',
						default = 5)
						
	# Sequence option.
	est_speed_increasing = 0
	age_increasing = 1
	bib_increasing = 2
	age_decreasing = 3
	bib_decreasing = 4
	series_decreasing = 5
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
		(_("Series"), (
				(series_decreasing, _("Series Rank")),
			),
		),
	)
	sequence_option = models.PositiveSmallIntegerField(
		verbose_name=_('Sequence Option'),
		choices = SEQUENCE_CHOICES,
		help_text = 'Criteria used to order participants in the wave',
		default=0 )
		
	series_for_seeding=models.ForeignKey( "Series", blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Series for Seeding'),
		help_text=_('Must be specified if Sequence Option is Series') )
	
	def save( self, *args, **kwargs ):
		init_sequence_last( WaveTT, self )
		return super( WaveTT, self ).save( *args, **kwargs )
	
	def get_results( self, category = None ):
		return super( WaveTT, self ).get_results( category ).select_related('participant', 'participant__license_holder')
	
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
		if self.sequence_option == self.series_decreasing and self.series_for_seeding:
			
			from .series_results import get_results_for_category		# import this here to avoid a circular dependency.

			licence_holder_series_rank = {}
			categories_seen = set()
			for category in self.categories.all():
				if category in categories_seen:
					continue
				categoryResult, events = get_results_for_category(self.series_for_seeding, category)
				for rank, r in enumerate(categoryResult, 1):
					licence_holder_series_rank[r[0].id] = rank
				# If this is category is scored as a group, record the group so we don't compute the series more than necessary.
				categories_seen.update( self.series_for_seeding.get_group_related_categories(category) )
				
			return lambda p: (
				p.seed_option,
				-licence_holder_series_rank.get(p.license_holder_id, 999999),	# If no rank in series, rank high and fallback to random.
				random.random(),	# Break ties randomly.
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
				p.license_holder.get_tt_metric(timezone.localtime(timezone.now()).date()),
				p.id,
			)
		elif self.sequence_option == self.age_decreasing:
			return lambda p: (
				p.seed_option,
				datetime.date(3000,1,1) - p.license_holder.date_of_birth,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(timezone.localtime(timezone.now()).date()),
				p.id,
			)
		elif self.sequence_option == self.bib_decreasing:
			return lambda p: (
				p.seed_option,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(timezone.localtime(timezone.now()).date()),
				p.id,
			)
		else:	# self.sequence_option == self.est_speed_increasing.
			return lambda p: (
				p.seed_option,
				p.est_kmh,
				-(p.bib or 0),
				p.license_holder.get_tt_metric(timezone.localtime(timezone.now()).date()),
				p.id,
			)
	
	@property
	def gap_rules_html( self ):
		summary = [u'<table>']
		try:
			for label, value in (
					(_('GapBefore'), self.gap_before_wave if self.gap_before_wave else None),
					(_('RegularGap'), self.regular_start_gap if self.regular_start_gap else None),
					(_('FastGap'), self.fastest_participants_start_gap if self.num_fastest_participants else None),
					(_('NumFast'), self.num_fastest_participants if self.num_fastest_participants else None),
				):
				if value is not None:
					summary.append( u'<tr><td class="text-right">{}&nbsp&nbsp</td><td class="text-right">{}</td><tr>'.format(label, u'{}'.format(value)) )
		except Exception as e:
			return e
		summary.append( '</table>' )
		return u''.join( summary )
	
	@property
	def gap_rules_text( self ):
		summary = []
		try:
			for label, value in (
					(_('GapBefore'), self.gap_before_wave if self.gap_before_wave else None),
					(_('RegularGap'), self.regular_start_gap if self.regular_start_gap else None),
					(_('FastGap'), self.fastest_participants_start_gap if self.num_fastest_participants else None),
					(_('NumFast'), self.num_fastest_participants if self.num_fastest_participants else None),
				):
				if value is not None:
					summary.append( u'{}={}'.format(label, u'{}'.format(value)) )
		except Exception as e:
			return e
		return u' '.join( summary )
	
	def get_participants( self ):
		participants = list( self.get_participants_unsorted().select_related('category', 'license_holder','team') )
		
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
		for i in range(1, len(participants)):
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
	
	def get_sequence_option_str( self ):
		if self.sequence_option == self.series_decreasing:
			return format_lazy( u'{}: {}', self.get_sequence_option_display(), self.series_for_seeding.name if self.series_for_seeding else _('Missing'))
		else:
			return self.get_sequence_option_display()
	
	def get_details_html( self, include_starters=False ):
		distance = None
		if self.distance:
			if self.laps:
				distance = self.distance * self.laps
			else:
				distance = self.distance
		
		details = [u'{:.2f}&nbsp;<strong>{}</strong>'.format(distance, self.distance_unit) if distance else None]
		if self.sequence_option == self.series_decreasing:
			details.append( u'{}: {}'.format( self.get_sequence_option_display(), self.series_for_seeding.name if self.series_for_seeding else _('Missing')) )
		else:
			details.append( self.get_sequence_option_display() )
		s = u', '.join( v for v in details if v )
		return s
	
	class Meta:
		verbose_name = _('TTWave')
		verbose_name_plural = _('TTWaves')
		ordering = ['sequence']

class ParticipantOption( models.Model ):
	competition = models.ForeignKey( Competition, db_index = True, on_delete=models.CASCADE )
	participant = models.ForeignKey( Participant, db_index = True, on_delete=models.CASCADE )
	option_id = models.PositiveIntegerField( verbose_name = _('Option Id') )
	
	@staticmethod
	@transaction.atomic
	def set_option_ids( participant, option_ids = [] ):
		ParticipantOption.objects.filter(competition=participant.competition, participant=participant).delete()
		if option_ids:
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
		for option_id, included in option_id_included.items():
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
		for id in range(1, 1000000):
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
# Series
#
def categories_from_pks( pks ):
	return sorted( (c for c in Category.objects.in_bulk(pks).values()), key=operator.attrgetter('sequence') )

class Series( Sequence ):
	name = models.CharField( max_length=32, default = 'MySeries', verbose_name=_('Name') )
	description = models.CharField( max_length=80, blank=True, default='', verbose_name=_('Description') )

	category_format = models.ForeignKey( CategoryFormat, db_index=True, on_delete=models.CASCADE )
	
	RANKING_CRITERIA = (
		(0, _('Points')),
		(1, _('Time')),
		(2, _("% Finish/Winning Time")),
	)
	ranking_criteria = models.PositiveSmallIntegerField( default=0, verbose_name = _('Ranking Criteria'), choices=RANKING_CRITERIA )
	
	show_last_to_first = models.BooleanField( default=True, verbose_name=_('Show Events Last to First') )
	
	TIE_BREAKING_RULE_CHOICES = (
		(5, _('Number of 1st, 2nd, 3rd, 4th then 5th place finishes')),
		(4, _('Number of 1st, 2nd, 3rd then 4th place finishes')),
		(3, _('Number of 1st, 2nd then 3rd place finishes')),
		(2, _('Number of 1st then 2nd place finishes')),
		(1, _('Number of 1st place finishes')),
		(0, _('Do not consider place finishes')),
	)
	tie_breaking_rule = models.PositiveSmallIntegerField( default=5, choices=TIE_BREAKING_RULE_CHOICES,
		verbose_name=_('Tie-breaking Rule')
	)
	consider_most_events_completed = models.BooleanField( default=False, verbose_name=_('Consider Most Events Completed') )
	
	consider_primes = models.BooleanField( default=True, verbose_name=_('Consider Points or Time Primes') )
	
	BEST_RESULTS_CHOICES = [(0, _('All Results')), (1, _('Best Result Only'))] + [
		(i, format_lazy(u'{} {}', i, _('Best Results Only'))) for i in range(2,31)
	]
	best_results_to_consider = models.PositiveSmallIntegerField( default=0, choices=BEST_RESULTS_CHOICES,
		verbose_name=_('Consider')
	)
	
	MUST_HAVE_COMPLETED_CHOICES = [(i, format_lazy('{} {}', i, _('or more Events'))) for i in range(31)]
	must_have_completed = models.PositiveSmallIntegerField( default=0, choices=MUST_HAVE_COMPLETED_CHOICES,
		verbose_name=_('Must have completed')
	)
	
	callup_max = models.PositiveSmallIntegerField( default=0, verbose_name=_('Callup Maximum') )
	randomize_if_no_results = models.BooleanField( default=False, verbose_name=_("Randomize callups if no results") )
	
	custom_category_names = models.TextField( default='', blank=True, verbose_name=_('Custom Categories') )
	
	def make_copy( self ):
		self_pk = self.pk
		collections = (
			self.seriesincludecategory_set.all(),
			self.seriespointsstructure_set.all(),
			self.seriesupgradeprogression_set.all(),
			self.categorygroup_set.all(),
			self.seriescompetitionevent_set.all(),	# This must be last.
		)
		
		series_new = self
		series_new.pk = None
		series_new.id = None
		series_new.name += timezone.now().strftime(' %Y-%m-%d %H:%M:%S')
		series_new.save()
		
		for collection in collections:
			for c in collection:
				c.make_copy( series_new )
		
		series_new.move_to( self.sequence )
		return series_new
	
	def get_container( self ):
		return Series.objects.all()
		
	def get_categories( self ):
		return [ic.category for ic in self.seriesincludecategory_set.all().select_related('category').only('category').order_by('category__sequence')]
		
	def get_categories_in_groups( self ):
		cats = set()
		for g in self.categorygroup_set.all():
			cats.update( g.get_categories() )
		return cats
		
	def get_categories_not_in_groups( self ):
		return sorted( set(self.get_categories()) - self.get_categories_in_groups(), key=operator.attrgetter('sequence') )
		
	def get_points_structures( self ):
		return self.seriespointsstructure_set.all().order_by('sequence')
		
	def get_upgrade_progressions( self ):
		return self.seriesupgradeprogression_set.all().order_by('sequence')
		
	def get_category_groups( self ):
		return self.categorygroup_set.all().order_by('sequence')
		
	def validate( self ):
		categories = self.get_categories()
		for collection in (
				self.seriespointsstructure_set.all(),
				self.seriesupgradeprogression_set.all(),
				self.categorygroup_set.all(),
				):
			validate_sequence( collection )
			for i, element in enumerate(collection):
				try:
					element.harmonize_categories( categories )
				except AttributeError:
					break
		
		ce_to_delete = []
		categories = set( categories )
		for ce in self.seriescompetitionevent_set.all():
			if set( ce.event.get_categories() ).isdisjoint( categories ):
				ce_to_delete.append( ce )
		for ce in ce_to_delete:
			ce.delete()
	
	def get_events_for_competition( self, competition ):
		events = [ce.event for ce in self.seriescompetitionevent_set.all().select_related('event_mass_start', 'event_tt') if ce.competition == competition]
		events.sort( key=operator.attrgetter('date_time') )
		return events
		
	def get_competitions( self ):
		return sorted( set(ce.competition for ce in self.seriescompetitionevent_set.all()), key=operator.attrgetter('start_date'), reverse=True )
	
	def remove_competition( self, competition ):
		for ce in [ce for ce in self.seriescompetitionevent_set.all() if ce.competition == competition]:
			ce.delete()
			
	def get_default_points_structure( self ):
		ps = self.seriespointsstructure_set.all().first()
		if not ps:
			ps = SeriesPointsStructure( series=self, name='SeriesPointsDefault' )
			ps.save()
		return ps
	
	def get_group_related_categories( self, category ):
		# If this category is part of a group, add all the group categories.
		for g in self.categorygroup_set.all():
			g_categories = g.get_categories()
			if category in g_categories:
				return g_categories
		return [category]
	
	def get_related_categories( self, category ):
		categories = self.get_categories()
		if category not in categories:
			return set()
		
		related_categories = set( self.get_group_related_categories(category) )
		
		# If any of these categories are in a progression, add all the progression categories.
		for p in self.seriesupgradeprogression_set.all():
			p_categories = set( p.get_categories() )
			if not related_categories.isdisjoint(p_categories):
				related_categories |= p_categories
		
		return related_categories
	
	def get_all_custom_category_names( self ):
		names = set()
		for ce in self.seriescompetitionevent_set.all():
			if   ce.event_mass_start:
				names |= { cc.name for cc in ce.event_mass_start.customcategorymassstart_set.all() }
			elif ce.event_tt:
				names |= { cc.name for cc in ce.event_tt.customcategorytt_set.all() }
		return sorted( names )
		
	def get_custom_category_names( self ):
		return self.custom_category_names.split( ',\n' )
		
	def __str__( self ):
		return self.name
	
	class Meta:
		verbose_name = _("Series")
		verbose_name_plural = _("Series")
		ordering = ['sequence']
		
#-----------------------------------------------------------------------
class SeriesPointsStructure( Sequence ):
	series = models.ForeignKey( Series, db_index=True, on_delete=models.CASCADE )
	name = models.CharField( max_length=32, default='SeriesPoints', verbose_name=_('Name') )
	
	points_for_place = models.CharField( max_length=512, default='30,25,20,15,10,5,3,1,1,1', verbose_name=_('Points for Place') )
	finish_points = models.PositiveSmallIntegerField( default=0, verbose_name=_('Finish Points') )
	dnf_points = models.PositiveSmallIntegerField( default=0, verbose_name=_('DNF Points') )
	dns_points = models.PositiveSmallIntegerField( default=0, verbose_name=_('DNS Points') )

	def make_copy( self, series_new ):
		self_pk = self.pk
		o_new = self
		o_new.pk = None
		o_new.id = None
		o_new.series = series_new
		o_new.save()
		return o_new

	def get_container( self ):
		return self.series.seriespointsstructure_set.all()
	
	reNonDigit = re.compile( r'[^\d]' )
	def save( self, *args, **kwargs ):
		pfp = [d for d in sorted((int(v) for v in self.reNonDigit.sub(' ', self.points_for_place).split() if v), reverse=True) if d]
		self.points_for_place = u','.join( '{}'.format(d) for d in pfp )
		if pfp:
			lowest_pfp = pfp[-1]
			for a in ('finish_points', 'dnf_points', 'dns_points'):
				setattr( self, a, min( getattr(self, a), lowest_pfp ) )
		self.dnf_points = min( self.dnf_points, self.finish_points )
		self.dns_points = min( self.dns_points, self.dnf_points )
		super( SeriesPointsStructure, self ).save( args, kwargs )

	@property
	def points_deep( self ):
		return self.points_for_place.count(',') + 1 if self.points_for_place else 0

	def get_points_getter( self ):
		pfp = [int(v) for v in self.reNonDigit.sub(' ', self.points_for_place).split()]
		def points_getter( rank, status=0 ):
			if not status:
				return pfp[rank-1] if rank <= len(pfp) else self.finish_points
			elif status == Result.cDNF:
				return self.dnf_points
			elif status == Result.cDNS:
				return self.dns_points
			return 0
		return points_getter

	def __str__( self ):
		f = [u'{}: Points for place: {}'.format( self.name, self.points_for_place )]
		if self.finish_points:
			f.append( u' finish={}'.format(self.finish_points) )
		if self.dnf_points:
			f.append(  u' dnf={}'.format(self.dnf_points) )
		if self.dns_points:
			f.append(  u' dns={}'.format(self.dns_points) )
		return u', '.join( f )
		
	class Meta:
		verbose_name = _("PointsStructure")
		verbose_name_plural = _("PointsStructures")

#-----------------------------------------------------------------------
class SeriesCompetitionEvent( models.Model ):
	series = models.ForeignKey( Series, db_index=True, on_delete=models.CASCADE )
	event_mass_start = models.ForeignKey( EventMassStart, on_delete=models.CASCADE, blank=True, null=True, default=None, db_index=True )
	event_tt = models.ForeignKey( EventTT, on_delete=models.CASCADE, blank=True, null=True, default=None, db_index=True )
	
	points_structure = models.ForeignKey( SeriesPointsStructure, blank=True, null=True, db_index=True, on_delete=models.CASCADE )
	
	def make_copy( self, series_new ):
		points_structure_new = (
			series_new.seriespointsstructure_set.filter( name=self.points_structure.name ).first()
			if self.points_structure else None
		)
		
		self_pk = self.pk
		o_new = self
		o_new.pk = None
		o_new.id = None
		o_new.series = series_new
		o_new.points_structure = points_structure_new
		o_new.save()
		return o_new

	@property
	def event( self ):
		return self.event_mass_start or self.event_tt

	@event.setter
	def event( self, e ):
		if e.event_type == 0:
			self.event_mass_start, self.event_tt = e, None
		else:
			self.event_mass_start, self.event_tt = None, e

	@property
	def competition( self ):
		return (self.event_mass_start or self.event_tt).competition

	def get_value_for_rank_func( self ):
		points_structure = self.points_structure if self.series.ranking_criteria == 0 else None
		if points_structure:
			get_points = points_structure.get_points_getter()
		else:
			get_points = None
		
		if get_points:
			if self.series.consider_primes:
				def get_value_for_rank( rr, rank, rr_winner ):
					return get_points( rank, rr.status ) + rr.points
			else:
				def get_value_for_rank( rr, rank, rr_winner ):
					return get_points( rank, rr.status )
		elif self.series.ranking_criteria == 1:	# Time
			if self.series.consider_primes:
				def get_value_for_rank( rr, rank, rr_winner ):
					if getattr(rr,'laps',0) != getattr(rr_winner,'laps',0):
						return None
					try:
						t = rr.finish_time.total_seconds()
					except:
						return None
					if rr.adjustment_time:
						t += rr.adjustment_time.total_seconds()
					if rr.time_bonus:
						t -= rr.time_bonus.total_seconds()
					return t
			else:
				def get_value_for_rank( rr, rank, rr_winner ):
					if getattr(rr,'laps',0) != getattr(rr_winner,'laps',0):
						return None
					try:
						t = rr.finish_time.total_seconds()
					except:
						return None
					if rr.adjustment_time:
						t += rr.adjustment_time.total_seconds()
					return t
		elif self.series.ranking_criteria == 2:	# % Winner / Time
			def get_value_for_rank( rr, rank, rr_winner ):
				if getattr(rr,'laps',0) != getattr(rr_winner,'laps',0):
					return None
				try:
					v = min( 100.0, 100.0 * (rr_winner.finish_time.total_seconds() / rr.finish_time.total_seconds()) )
				except:
					v = 0
				return v
		else:
			assert False, 'Unknown ranking criteria'
			
		return get_value_for_rank
		
	class Meta:
		verbose_name = _("SeriesCompetitionEvent")
		verbose_name_plural = _("SeriesCompetitionEvents")
	
#-----------------------------------------------------------------------
class UpdateLog( models.Model ):
	created = models.DateTimeField( auto_now_add=True, db_index=True, verbose_name=_('Created') )
	UPDATE_TYPE_CHOICES = (
		(0,_('MergeLicenseHolders')),
		(1,_('MergeTeams')),
	)
	update_type = models.PositiveSmallIntegerField( choices=UPDATE_TYPE_CHOICES, verbose_name=_('Update Type') )
	description = models.TextField( verbose_name=_('Description') )
	
	@property
	def description_html( self ):
		html = []
		for i, d in enumerate(self.description.split(u'\n')):
			if i != 0:
				html.append( u'<br/>' )
			html.append( escape(d) )
		return mark_safe( u''.join(html) )
	
	class Meta:
		verbose_name = _("UpdateLog")
		verbose_name_plural = _("UpdateLog")
		ordering = ['-created']

#-----------------------------------------------------------------------
class SeriesIncludeCategory( models.Model ):
	# Selects which Categories are to be part of the Series.
	series = models.ForeignKey( Series, db_index=True, on_delete=models.CASCADE )
	category = models.ForeignKey( Category, db_index=True, on_delete=models.CASCADE )
	
	def make_copy( self, series_new ):
		self_pk = self.pk
		o_new = self
		o_new.pk = None
		o_new.id = None
		o_new.series = series_new
		o_new.save()
		return o_new

	class Meta:
		verbose_name = _("SeriesIncludeCategory")
		verbose_name_plural = _("SeriesIncludeCategories")
		ordering = ['category__sequence']

class CategoryGroup( Sequence ):
	# Used to create Category groups for a combined category Series.
	name = models.CharField( max_length=32, default='MyGroup', verbose_name=_('Name') )
	series = models.ForeignKey( Series, db_index=True, on_delete=models.CASCADE )
	
	def make_copy( self, series_new ):
		categories = self.get_categories()
		
		self_pk = self.pk
		o_new = self
		o_new.pk = None
		o_new.id = None
		o_new.series = series_new
		o_new.save()
		
		CategoryGroupElement.objects.bulk_create( [CategoryGroupElement(category_group=o_new, category=c) for c in categories] )
		return o_new

	def get_container( self ):
		return self.series.categorygroup_set.all()
	
	def harmonize_categories( self, allowed_categories ):
		self.categorygroupelement_set.exclude( category__in=allowed_categories ).delete()
	
	def get_categories( self ):
		return [cge.category for cge in self.categorygroupelement_set.all().select_related('category').only('category').order_by('category__sequence')]
	
	def get_text( self ):
		text = []
		for cge in self.categorygroupelement_set.all():
			text.extend( [cge.category.code_gender, ', '] )
		if text:
			text = text[:-1]
		return u''.join( text )
	
	class Meta:
		verbose_name = _("CategoryGroup")
		verbose_name_plural = _("CategoryGroups")

class CategoryGroupElement( models.Model ):
	category_group = models.ForeignKey( CategoryGroup, db_index=True, on_delete=models.CASCADE )
	category = models.ForeignKey( Category, db_index=True, on_delete=models.CASCADE )
	
	class Meta:
		verbose_name = _("CategoryGroupElement")
		verbose_name_plural = _("CategoryGroupElements")
		ordering = ['category__sequence']

#-----------------------------------------------------------------------
class SeriesUpgradeProgression( Sequence ):
	series = models.ForeignKey( Series, db_index=True, on_delete=models.CASCADE )
	factor = models.FloatField( default=0.5, verbose_name = _('Factor') )

	def make_copy( self, series_new ):
		categories = self.get_categories()
		
		self_pk = self.pk
		o_new = self
		o_new.pk = None
		o_new.id = None
		o_new.series = series_new
		o_new.save()
		
		SeriesUpgradeCategory.objects.bulk_create( [		
			SeriesUpgradeCategory(upgrade_progression=o_new, category=c, sequence=i) for i, c in enumerate(categories)
		] )
		return o_new

	def get_container( self ):
		return self.series.seriesupgradeprogression_set.all()
	
	def get_text( self ):
		s = []
		for uc in self.seriesupgradecategory_set.all().select_related('category'):
			c = uc.category
			s.extend( [c.get_gender_display(), '-', c.code, ',  '] )
		
		if not s:
			return _('Empty')
		s = s[:-1]
		return format_lazy( u'{}'*len(s), *s )
		
	def harmonize_categories( self, allowed_categories ):
		self.seriesupgradecategory_set.exclude( category__in=allowed_categories ).delete()
		
	def get_categories( self ):
		return [ce.category for ce in self.seriesupgradecategory_set.all().select_related('category').only('category')]
	
	def save( self, *args, **kwargs ):
		if self.factor > 1.0 or self.factor < 0.0:
			self.factor = 0.5
		super( SeriesUpgradeProgression, self ).save( *args, **kwargs )
	
	class Meta:
		verbose_name = _("SeriesUpgradeProgression")
		verbose_name_plural = _("SeriesUpgradeProgressions")
	
class SeriesUpgradeCategory( Sequence ):
	upgrade_progression = models.ForeignKey( SeriesUpgradeProgression, db_index=True, on_delete=models.CASCADE )
	category = models.ForeignKey( Category, db_index=True, on_delete=models.CASCADE )
	
	def get_container( self ):
		return self.upgrade_progression.seriesupgradecategory_set.all()
	
	class Meta:
		verbose_name = _("SeriesUpgradeCategory")
		verbose_name_plural = _("SeriesUpgradeCategories")
	
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------

@receiver( pre_delete, sender=EventMassStart )
@receiver( pre_delete, sender=EventTT )
def clean_up_event_option_id( sender, **kwargs ):
	event = kwargs.get('instance', None)
	if event and event.optional:
		ParticipantOption.objects.filter(competition=event.competition, option_id=event.option_id).delete()

#-------------------------------------------------------------------------------------

def license_holder_merge_duplicates( license_holder_merge, duplicates ):
	duplicates = list( set(list(duplicates) + [license_holder_merge]) )
	license_holder_duplicate_pks = [lh.pk for lh in duplicates if lh != license_holder_merge]
	if not license_holder_duplicate_pks:
		return

	#-------------------------------------------------------------------
	# Record the merge in the log.
	def get_lh_info( lh ):
		return u'"{}" license="{}" uciid="{}" dob={} gender={}\n'.format(
			lh.full_name(),
			lh.license_code_trunc,
			lh.get_uci_id_text(),
			lh.date_of_birth.strftime('%Y-%m-%d'),
			lh.get_gender_display()
		)
	
	description = StringIO()
	for lh in LicenseHolder.objects.filter( pk__in=license_holder_duplicate_pks ):
		description.write( get_lh_info(lh) )
	description.write( u'--->\n' )
	lh = license_holder_merge
	description.write( get_lh_info(lh) )
	UpdateLog( update_type=0, description=description.getvalue() ).save()
	description.close()
	
	#-------------------------------------------------------------------
	# Change duplicate participants to point back to the correct license holder.
	for p in Participant.objects.filter( license_holder__pk__in=license_holder_duplicate_pks ):
		# Ensure we don't create an integrity error if the license_holder_merge is already entered in this category.
		if not Participant.objects.filter(competition=p.competition, category=p.category, license_holder=license_holder_merge).exists():
			p.license_holder = license_holder_merge
			p.save()
	
	'''
	#-------------------------------------------------------------------
	# Cache and delete the Participant Options.
	participant_options = [(po.participant.pk, po) for po in ParticipantOption.objects.filter( participant__license_holder__pk__in=[lh.pk for lh in duplicates] ) ]
	for participant_pk, po in participant_options:
		po.delete()
	
	# Cache the participants and results.
	participant_license_holder_duplicate_pks = Participant.objects.filter(license_holder__pk__in=[lh.pk for lh in duplicates]).values_list('pk', flat=True)
	participants = list(Participant.objects.filter(pk__in=participant_license_holder_duplicate_pks))
	entry_tt = list(EntryTT.objects.filter(participant__pk__in=participant_license_holder_duplicate_pks))
	results_mass_start = list(ResultMassStart.objects.filter(participant__pk__in=participant_license_holder_duplicate_pks))
	results_tt = list(ResultTT.objects.filter(participant__pk__in=participant_license_holder_duplicate_pks))
	
	# Delete the participants.
	participants.sort( key = lambda p: 0 if p.license_holder == license_holder_merge else 1 )
	for p in participants:
		p.delete()
		
	# Add back Participants to point to the merged license_holder.
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
	
	# Add back the tt entries.
	events_seen = set()
	for ett in entry_tt:
		if ett.event_id not in events_seen:
			ett.pk = None
			try:
				ett.participant = participant_map[ett.participant_id]
			except KeyError:
				continue
			ett.save()
			events_seen.add( ett.event_id )

	# Add back the results.  Ensure that there is only one result per event for each license holder.
	events_seen = set()
	for results in [results_mass_start, results_tt]:
		for r in results:
			if r.event_id not in events_seen:
				r.pk = None
				try:
					r.participant = participant_map[r.participant_id]
				except KeyError:
					continue
				r.save()
				events_seen.add( r.event_id )
	'''	
	
	#--------------------------------------------------------------------
	# Ensure the merged entry is added to every Seasons Pass held by a duplicate.
	# Get all the seasons passes held by any duplicate (includes the license holder)
	# Resolve these to memory as lazy evaluation won't work after the delete tbat follows.
	seasons_passes = set(
		SeasonsPass.objects.filter( pk__in=SeasonsPassHolder.objects.filter(license_holder__pk__in=[lh.pk for lh in duplicates]).values('seasons_pass__pk').distinct() )
	)
	# Remove the duplicates from all season's passes.
	SeasonsPassHolder.objects.filter( license_holder__pk__in=[lh.pk for lh in duplicates] ).delete()
	# Add the representative license holder to all the seasons passes held by any duplicate.
	SeasonsPassHolder.objects.bulk_create( [SeasonsPassHolder(seasons_pass=sp, license_holder=license_holder_merge) for sp in seasons_passes] )
	
	# Ensure that numbers in the number set are owned by the remaining license_holder.
	for ns in NumberSet.objects.all():
		nse_existing = list( NumberSetEntry.objects.filter(number_set=ns, license_holder__pk__in=license_holder_duplicate_pks).values_list('bib', 'date_lost') )
		NumberSetEntry.objects.filter(number_set=ns, license_holder__pk__in=license_holder_duplicate_pks).delete()
		for bib, date_lost in nse_existing:
			if not NumberSetEntry.objects.filter( number_set=ns, bib=bib ).exists():
				NumberSetEntry( number_set=ns, bib=bib, license_holder=license_holder_merge, date_lost=date_lost ).save()
	
	# Combine waivers.  Preserve most recent date_signed for all legal entities.
	for w in Waiver.objects.filter( license_holder__pk__in=license_holder_duplicate_pks ):
		w_merge = Waiver.objects.filter( license_holder=license_holder_merge, legal_entity=w.legal_entity ).first()
		if not w_merge:								# Add waiver if it doesn't exist.
			Waiver( license_holder=license_holder_merge, legal_entity=w.legal_entity, date_signed=w.date_signed ).save()
		elif w_merge.date_signed < w.date_signed:	# Else update to more recent date signed if necessary.
			w_merge.date_signed = w.date_signed
			w_merge.save()
	
	# Final delete.  Cascade delete will clean up all old SeasonsPass and Waiver entries.
	LicenseHolder.objects.filter( pk__in=license_holder_duplicate_pks ).delete()
	
#-----------------------------------------------------------------------------------------------
class CompetitionCategoryOption(models.Model):
	competition = models.ForeignKey( Competition, db_index=True, on_delete=models.CASCADE )
	category = models.ForeignKey( Category, db_index=True, on_delete=models.CASCADE )
	
	license_check_required = models.BooleanField( default=False, verbose_name=_("License Check Required") )
	note = models.CharField( max_length=160, default='', blank=True, verbose_name=_('Note') )
	
	@staticmethod
	def normalize( competition ):
		categories = competition.category_format.category_set.all()
		ccos = competition.competitioncategoryoption_set.all()
		ccos.exclude( category__in=categories ).delete()
		CompetitionCategoryOption.objects.bulk_create( [
			CompetitionCategoryOption(competition=competition, category=category)
			for category in categories.exclude( id__in=ccos.values('category__id') )
		] )
	
	@staticmethod
	def is_license_check_required( competition, category ):
		cco = CompetitionCategoryOption.objects.filter( competition=competition, category=category ).first()
		return cco and cco.license_check_required
	
	def save( self, *args, **kwargs ):
		self.note = self.note.strip()
		return super(CompetitionCategoryOption, self).save( *args, **kwargs )
		
	def make_copy( self, competition_new ):
		cco_new = self
		cco_new.pk = None
		cco_new.competition = competition_new
		cco_new.save()
	
	class Meta:
		verbose_name = _('CompetitionCategoryOption')
		unique_together = (("competition", "category"),)

#-----------------------------------------------------------------------------------------------
class LicenseCheckState(models.Model):
	license_holder = models.ForeignKey( LicenseHolder, db_index=True, on_delete=models.CASCADE )
	category = models.ForeignKey( Category, db_index=True, on_delete=models.CASCADE )
	discipline = models.ForeignKey( Discipline, db_index=True, default=1, on_delete=models.CASCADE )
	report_label_license_check = models.ForeignKey( ReportLabel, db_index=True, on_delete=models.CASCADE )
	check_date = models.DateField( db_index=True )
	
	@staticmethod
	def check_participant( participant ):
		q = Participant.objects.filter(
			license_holder__id=participant.license_holder_id,
			category__id=participant.category_id,
			license_checked=True,
			competition__discipline__id=participant.competition.discipline.id,
			competition__start_date__gte=datetime.date(participant.competition.start_date.year,1,1),
			competition__start_date__lte=participant.competition.start_date,
			competition__report_label_license_check=participant.competition.report_label_license_check,
		)
		if q.exists():
			return True
		q = LicenseCheckState.objects.filter(
			license_holder__id=participant.license_holder_id,
			category__id=participant.category_id,
			discipline__id=participant.competition.discipline.id,
			report_label_license_check=participant.competition.report_label_license_check,
			check_date__gte=datetime.date(participant.competition.start_date.year,1,1),
			check_date__lte=participant.competition.start_date,
		)
		return q.exists()

	@staticmethod
	def uncheck_participant( participant ):
		LicenseCheckState.objects.filter(
			license_holder__id=participant.license_holder_id,
			category__id=participant.category_id,
			discipline__id=participant.competition.discipline_id,
			report_label_license_check=participant.competition.report_label_license_check,
			check_date__gte=datetime.date(participant.competition.start_date.year,1,1),
			check_date__lte=participant.competition.start_date,
		).delete()
		Participant.objects.filter(
			license_holder__id=participant.license_holder_id,
			competition__discipline__id=participant.competition.discipline_id,
			category__id=participant.category_id,
			license_checked=True,
			competition__start_date__gte=datetime.date(participant.competition.start_date.year,1,1),
			competition__start_date__lte=participant.competition.start_date,
			competition__report_label_license_check=participant.competition.report_label_license_check,
		).update( license_checked=False )
	
	def key( self ):
		return self.license_holder_id, self.category_id, self.discipline_id, self.report_label_license_check_id
		
	@staticmethod
	def refresh():
		def participant_key( p ):
			return p.license_holder_id, p.category_id, p.competition.discipline_id, p.competition.report_label_license_check_id
	
		year_cur = datetime.datetime.now().year
		LicenseCheckState.objects.filter( check_date__lt=datetime.date(year_cur, 1, 1) ).delete()
		
		to_delete = []
		csd = {}
		for cs in LicenseCheckState.objects.all().order_by('-check_date'):
			key = cs.key()
			if key not in csd:
				csd[key] = cs.check_date
			else:
				to_delete.append( cs.id )	# Delete redundant license checks.
		
		while to_delete:
			with transaction.atomic():
				LicenseCheckState.objects.filter( id__in=to_delete[-256:] ).delete()
			del to_delete [-256:]
		
		to_add = []
		to_update = {}
		for p in Participant.objects.filter(
				license_checked=True, category__isnull=False,
				competition__report_label_license_check__isnull=False,
				competition__start_date__gte=datetime.date(year_cur,1,1),
				competition__start_date__lte=datetime.date.today(),
			).defer('signature',
			).select_related('competition','category','competition__discipline','competition__report_label_license_check',
			).order_by('-competition__start_date'):
			key = participant_key( p )
			if key not in csd:
				to_add.append( LicenseCheckState(
					license_holder=p.license_holder,
					category=p.category,
					discipline=p.competition.discipline,
					report_label_license_check=p.competition.report_label_license_check,
					check_date=p.competition.start_date )
				)
				csd[key] = p.competition.start_date
			elif csd[key] < p.competition.start_date:
				to_update[key] = p.competition.start_date
				csd[key] = p.competition.start_date
		
		# Update existing records to the most recent check date.
		to_update = [(k,v) for k,v in to_update.items()]
		while to_update:
			with transaction.atomic():
				for (license_holder_id, category_id, discipline_id, report_label_license_check_id), d in to_update[-256:]:
					LicenseCheckState.objects.filter(
						license_holder__id=license_holder_id,
						category__id = category_id,
						discipline__id = discipline_id,
						report_label_license_check__id=report_label_license_check_id ).update(check_date=d)
			del to_update[-256:]
			
		# Add the new license check dates.
		LicenseCheckState.objects.bulk_create( to_add )
		
#-----------------------------------------------------------------------------------------------
def truncate_char_fields( obj ):
	for f in type(obj)._meta.get_fields():
		if isinstance(f, models.CharField) and len(getattr(obj, f.name) or u'') > f.max_length:
			v = getattr( obj, f.name )
			setattr( obj, f.name, v[:f.max_length] )
	return obj
			
#-----------------------------------------------------------------------------------------------
# Apply upgrades.
#
'''
def bad_data_test():
	fields = dict(
		last_name = '00-TEST-LAST-NAME',
		first_name = '00-TEST-FIRST-NAME',
		date_of_birth = timezone.localtime(timezone.now()).date(),
	
		license_code = '0000{}'.format( random.randint(0,10000) ),
	
		existing_tag = '0000{}'.format( random.randint(0,10000) ),
		existing_tag2 = '0000{}'.format( random.randint(0,10000) ),
	)
	
	# Use bulk create to avoid calling the save method (otherwise data validation would take place)
	LicenseHolder.objects.bulk_create([
		LicenseHolder( **fields ),
	] )
	safe_print( list(LicenseHolder.objects.filter(last_name='00-TEST-LAST-NAME')) )
'''

def fix_bad_category_hints():
	safe_print( u'fix_bad_category_hints...' )
	CategoryHint.objects.all().exclude(discipline__id__in=Discipline.objects.all().values_list('id',flat=True)).delete()

def fix_phone_numbers():
	safe_print( u'fix_phone_numbers...' )
	with BulkSave() as bs:
		for lh in LicenseHolder.objects.filter(Q(phone__endswith='.0') | Q(emergency_contact_phone__endswith='.0')):
			if lh.phone and lh.phone.endswith('.0'):
				lh.phone = lh.phone[:-2]
			if lh.emergency_contact_phone and lh.emergency_contact_phone.endswith('.0'):
				lh.emergency_contact_phone = lh.emergency_contact_phone[:-2]
			bs.append( lh )
	with BulkSave() as bs:
		for t in Team.objects.filter(contact_phone__endswith='.0'):
			t.contact_phone = t.contact_phone[:-2]
			bs.append( t )
	
def fix_bad_license_codes():
	safe_print( u'fix_bad_license_codes and emergency contacts...' )
	q = (
		Q(license_code__startswith='0') | Q(existing_tag__startswith='0') | Q(existing_tag2__startswith='0') |
		Q(emergency_contact_name='0.0') | Q(emergency_contact_phone='0')
	)
	with BulkSave() as bs:
		for lh in LicenseHolder.objects.filter(q):
			bs.append( lh )
	
	q = Q(tag__startswith='0') | Q(tag2__startswith='0')
	with BulkSave() as bs:
		for p in Participant.objects.filter(q):
			bs.append( p )

def fix_non_unique_number_set_entries():
	safe_print( u'fix_non_unique_number_set_entries...' )
	for ns in NumberSet.objects.all():
		ns.validate()

def fix_nation_code():
	safe_print( u'fix_nation_codes...' )
	with BulkSave() as bs:
		for lh in LicenseHolder.objects.filter(nation_code__exact='').exclude(uci_code__exact=''):
			if lh.uci_code[:3].upper() in uci_country_codes_set:
				bs.append( lh )

def models_fix_data():
	fix_bad_license_codes()
	fix_nation_code()
	fix_non_unique_number_set_entries()
	fix_bad_category_hints()
	fix_phone_numbers()



