from django.db import models
from django.db import transaction
from django.db.models import Max
from django.db.models import Q

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.utils.timezone import get_default_timezone
from django.core.exceptions import ObjectDoesNotExist

from DurationField import DurationField
from get_abbrev import get_abbrev

import math
import datetime
import base64
from django.utils.translation import ugettext_lazy as _
import utils
import random
import iso3166
from TagFormat import getValidTagFormatStr, getTagFormatStr

def fixNullUpper( s ):
	if not s:
		return None
	s = (s or u'').strip()
	if s:
		return s.upper()
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
	base_name = cur_name
	suffix = u' - Copy('
	if suffix in base_name:
		base_name = base_name[:base_name.index(suffix)]
	for i in xrange(1, 100000):
		new_name = u'{}{}{})'.format( base_name, suffix, i )
		if not Competition.objects.filter(name = new_name).exists():
			return new_name
	return None

#----------------------------------------------------------------------------------------
class SystemInfo(models.Model):
	tag_template = models.CharField( max_length = 24, verbose_name = _('Tag Template'), help_text=_("Template for generating EPC RFID tags.") )

	RFID_SERVER_HOST_DEFAULT = 'localhost'
	RFID_SERVER_PORT_DEFAULT = 50111
	
	rfid_server_host = models.CharField( max_length = 32, default = RFID_SERVER_HOST_DEFAULT, verbose_name = _('RFID Reader Server Host')  )
	rfid_server_port = models.PositiveSmallIntegerField( default = RFID_SERVER_PORT_DEFAULT, verbose_name = _('RFID Reader Server Port') )
	
	@classmethod
	def get_tag_template_default( cls ):
		tNow = datetime.datetime.now()
		rs = ''.join( '0123456789ABCDEF'[random.randint(1,15)] for i in xrange(4))
		tt = '{}######{:02}'.format( rs, tNow.year % 100 )
		return tt
	
	@classmethod
	def get_singleton( cls ):
		if not cls.objects.exists():
			system_info = cls( tag_template = cls.get_tag_template_default() )
			system_info.save()
			return system_info
		else:
			for system_info in cls.objects.all():
				return system_info
	
	def save( self, *args, **kwargs ):
		self.tag_template = getValidTagFormatStr( self.tag_template )
		self.rfid_server_host = (self.rfid_server_host or self.RFID_SERVER_HOST_DEFAULT)
		self.rfid_server_port = (self.rfid_server_port or self.RFID_SERVER_PORT_DEFAULT)
		
		super(SystemInfo, self).save( *args, **kwargs )
		
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
	sequence = models.PositiveSmallIntegerField( default = lambda:Category.objects.count(), verbose_name = _('Sequence') )
	
	def make_copy( self, category_format ):
		category_new = self
		
		category_new.pk = None
		category_new.format = category_format
		category_new.save()
		return category_new
	
	def full_name( self ):
		return ', '.join( [self.code, self.get_gender_display(), self.description] )
		
	def get_search_text( self ):
		return utils.normalizeSearch(' '.join( u'"{}"'.format(f) for f in [self.code, self.get_gender_display(), self.description] ) )
		
	def __unicode__( self ):
		return u'{} ({}) [{}]'.format(self.code, self.description, self.format.name)
	
	class Meta:
		verbose_name = _('Category')
		verbose_name_plural = _("Categories")
		ordering = ['sequence', '-gender', 'code']

#---------------------------------------------------------------------------------

class Discipline(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = lambda:Discipline.objects.count() )
	
	def __unicode__( self ):
		return self.name
		
	class Meta:
		verbose_name = _('Discipline')
		verbose_name_plural = _('Disciplines')
		ordering = ['sequence', 'name']

class RaceClass(models.Model):
	name = models.CharField( max_length = 64 )
	sequence = models.PositiveSmallIntegerField( verbose_name = _('Sequence'), default = lambda:RaceClass.objects.count() )
	
	def __unicode__( self ):
		return self.name

	class Meta:
		verbose_name = _('Race Class')
		verbose_name_plural = _('Race Classes')
		ordering = ['sequence', 'name']

class NumberSet(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	sequence = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Sequence'), default = lambda:NumberSet.objects.count() )

	def __unicode__( self ):
		return self.name
	
	class Meta:
		verbose_name = _('Number Set')
		verbose_name_plural = _('Number Sets')
		ordering = ['sequence']

class Competition(models.Model):
	name = models.CharField( max_length = 64, verbose_name = _('Name') )
	description = models.CharField( max_length = 80, default = '', blank = True, verbose_name=_('Description') )
	
	number_set = models.ForeignKey( NumberSet, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_('Number Set') )
	
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
	
	def save(self, *args, **kwargs):
		''' If the start_date has changed, automatically update all the event dates too. '''
		if self.pk:
			try:
				competition_original = Competition.objects.get( pk = self.pk )
			except Exceptione as e:
				competition_original = None
			if competition_original and competition_original.start_date != self.start_date:
				time_delta = (
					datetime.datetime.combine(self.start_date, datetime.time(0,0,0)) -
					datetime.datetime.combine(competition_original.start_date, datetime.time(0,0,0))
				)
				self.adjust_event_times( time_delta )
			
		super(Competition, self).save(*args, **kwargs)
	
	@transaction.atomic
	def make_copy( self ):
		category_numbers = self.categorynumbers_set.all()
		event_mass_starts = self.eventmassstart_set.all()
	
		competition_new = self
		competition_new.pk = None
		competition_new.start_date = datetime.date.today()
		competition_new.save()
		
		for cn in category_numbers:
			cn.make_copy( competition_new )
		for e in event_mass_starts:
			e.make_copy( competition_new )
		
		return competition_new
		
	def adjust_event_times( self, time_delta ):
		for e in self.eventmassstart_set.all():
			e.date_time += time_delta
			e.save()
	
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
	
	def full_name( self ):
		return ' '.join( [self.name, self.organizer] )
		
	def get_search_text( self ):
		return utils.get_search_text( [self.name, self.organizer] )
	
	def get_events( self ):
		events = list( EventMassStart.objects.filter(competition = self) )
		#events.extend( list(EventTimeTrial.objects.filter(competition = self)) )
		events.sort( key = lambda e: e.date_time )
		return events
		
	def get_categories( self ):
		return Category.objects.filter( format = self.category_format )
	
	#----------------------------------------------------------------------------------------------------

	def get_categories_with_numbers( self ):
		category_lookup = set( c.id for c in Category.objects.filter(format = self.category_format) )
		categories = []
		for cn in self.categorynumbers_set.all():
			categories.extend( list(c for c in cn.categories.all() if c.id in category_lookup) )
		return sorted( set(categories), key = lambda c: c.sequence )
		return categories
	
	def get_categories_without_numbers( self ):
		categories_all = set( c for c in Category.objects.filter(format = self.category_format) )
		categories_with_numbers = set( self.get_categories_with_numbers() )
		categories_without_numbers = categories_all - categories_with_numbers
		return sorted( categories_without_numbers, key = lambda c: c.sequence )
	
	def get_category_numbers( self, category ):
		for cn in CategoryNumbers.objects.filter( competition = self, categories__in = [category] ):
			return cn
		return None
	
	#----------------------------------------------------------------------------------------------------

	def competition_age( self, license_holder ):
		# For cyclocross races between September and December,
		# use the next year as the competition age, not the current year.
		age = self.start_date.year - license_holder.date_of_birth.year
		if 'cyclo' in self.discipline.name.lower() and 9 <= self.start_date.month <= 12:
			age += 1
		return age
	
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
		return u', '.join( c.code for c in self.get_category_list() )
	
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
			
			if p.startswith( '-' ):
				exclude = True
				p = p[1:]
			else:
				exclude = False
				
			pair = p.split( '-' )
			if len(pair) == 1:
				n = int(pair[0])
				if exclude:
					include.discard( n )
				else:
					include.add( n )
			else:
				nBegin, nEnd = [int(v) for v in pair[:2]]
				nEnd = min( nEnd, 10000 )
				if exclude:
					include.difference_update( xrange(nBegin, nEnd+1) )
				else:
					include.update( xrange(nBegin, nEnd+1) )
		self.numbers = include
		return include
	
	def get_numbers( self ):
		if self.numCache is None or self.range_str_cache != self.range_str:
			self.numCache = self.getNumbersWorker()
			self.range_str_cache = self.range_str
		return self.numCache
	
	def __contains__( self, n ):
		return n in self.getNumbers()
		
	def save(self, *args, **kwargs):
		self.normalize()
		super(CategoryNumbers, self).save( *args, **kwargs )
		
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
	
	def __unicode__( self ):
		return u'%s, %s (%s)' % (self.date_time, self.name, self.competition.name)
		
	class Meta:
		verbose_name = _('Event')
		verbose_name_plural = _('Events')
		ordering = ['date_time']
		abstract = True

#---------------------------------------------------------------------------------------------------------

class EventMassStart( Event ):
	# Required for each event subclass.
	# penalties = generic.GenericRelation('Penalty')
	# observations = generic.GenericRelation('Observation')
	# kom_points = generic.GenericRelation('KOMPoints')
	# sprint_points = generic.GenericRelation('SprintPoints')
	# time_bonuses = generic.GenericRelation('TimeBonus')
	
	def make_copy( self, competition_new ):
		time_diff = self.date_time - datetime.datetime.combine(self.competition.start_date, datetime.time(0,0,0)).replace(tzinfo = get_default_timezone())
		waves = self.wave_set.all()
		
		event_mass_start_new = self
		event_mass_start_new.pk = None
		event_mass_start_new.competition = competition_new
		event_mass_start_new.date_time = datetime.datetime.combine(competition_new.start_date, datetime.time(0,0,0)).replace(tzinfo = get_default_timezone()) + time_diff
		event_mass_start_new.save()
		for w in waves:
			w.make_copy( event_mass_start_new )
		return event_mass_start_new
	
	def get_duplicate_bibs( self ):
		duplicates = []
		for w in self.wave_set.all():
			bibParticipant = {}
			for c in w.categories.all():
				for p in Participant.objects.filter( competition = self.competition, category = c, bib__isnull = False ):
					if p.bib in bibParticipant:
						duplicates.append( _('{}: {} ({}) and {} ({}) have duplicate Bib {}').format(
							w.name,
							bibParticipant[p.bib].name, bibParticipant[p.bib].category.code,
							p.name, p.category.code, p.bib) )
					else:
						bibParticipant[p.bib] = p
		return duplicates
		
	#----------------------------------------------------------------------------------------------------
	
	def get_potential_duplicate_bibs( self ):
		categories = set()
		for w in self.wave_set.all():
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
		category_lookup = set( c.id for c in Category.objects.filter(format = self.competition.category_format) )
		categories = []
		for wave in self.wave_set.all():
			categories.extend( list(c for c in wave.categories.all() if c.id in category_lookup) )
		return sorted( set(categories), key = lambda c: c.sequence )
	
	def get_categories_without_wave( self ):
		categories_all = set( c for c in Category.objects.filter(format = self.competition.category_format) )
		categories_with_wave = set( self.get_categories_with_wave() )
		categories_without_wave = categories_all - categories_with_wave
		return sorted( categories_without_wave, key = lambda c: c.sequence )
	
	def get_participant_count( self ):
		return sum( w.get_participant_count() for w in self.wave_set.all() )

	@property
	def wave_text( self ):
		return u', '.join( u'{} ({})'.format(w.name, w.category_text) for w in self.wave_set.all() )
	
	@property
	def wave_text_html( self ):
		return u'<br/>'.join( u'<strong>{}</strong>:&nbsp;&nbsp;{}'.format(w.name, w.category_text) for w in self.wave_set.all() )
	
	class Meta:
		verbose_name = _('Mass Start Event')
		verbose_name_plural = _('Mass Starts Event')
	
class Wave( models.Model ):
	event = models.ForeignKey( EventMassStart, db_index = True )
	
	name = models.CharField( max_length = 32 )
	categories = models.ManyToManyField( Category, verbose_name = _('Categories') )
	
	start_offset = DurationField( default = 0, verbose_name = _('Start Offset') )
	
	distance = models.FloatField( null = True, blank = True, verbose_name = _('Distance') )
	laps = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Laps') )
	minutes = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Race Minutes') )
	
	@property
	def distance_unit( self ):
		return self.event.competition.get_distance_unit_display() if self.event else ''
	
	def make_copy( self, event_new ):
		categories = self.categories.all()
		wave_new = self
		wave_new.pk = None
		wave_new.event = event_new
		wave_new.save()
		wave_new.categories = categories
		return wave_new
	
	def get_category_format( self ):
		return self.event.competition.category_format
	
	def get_start_time( self ):
		return self.event.date_time + self.start_offset
	
	def get_potential_duplicate_bibs( self ):
		if not self.id:
			return []
		competition = self.event.competition
		
		other_categories = set()
		my_categories = set()
		for w in self.event.wave_set.all():
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
		
		other_bibs = set.union( *[c.get_numbers() for c in other_category_numbers] )
		my_bibs = set.union( *[c.get_numbers() for c in my_category_numbers] )
		
		return sorted( other_bibs & my_bibs )
	
	def get_participants( self ):
		return Participant.objects.filter( competition=self.event.competition, category__in=self.categories.all() ).order_by( 'bib' )
	
	def get_participant_count( self ):
		return Participant.objects.filter( competition=self.event.competition, category__in=self.categories.all() ).count()
	
	@property
	def category_text( self ):
		return u', '.join( category.code for category in sorted(self.categories.all(), key=lambda c: c.sequence) )
	
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
		super(Team, self).save( *args, **kwargs )
	
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

class LicenseHolder(models.Model):
	last_name = models.CharField( max_length=64, verbose_name=_('Last Name'), db_index=True )
	first_name = models.CharField( max_length=64, verbose_name=_('First Name'), db_index=True )
	
	GENDER_CHOICES=(
		(0, _('Men')),
		(1, _('Women')),
	)
	gender = models.PositiveSmallIntegerField( choices=GENDER_CHOICES, default=0 )
	
	date_of_birth = models.DateField()
	
	city = models.CharField( max_length=64, blank=True, default='', verbose_name=_('City') )
	state_prov = models.CharField( max_length=64, blank=True, default='', verbose_name=_('State/Prov') )
	nationality = models.CharField( max_length=64, blank=True, default='', verbose_name=_('Nationality') )
	
	email = models.EmailField( blank=True )
	
	uci_code = models.CharField( max_length=11, blank=True, default='', db_index=True, verbose_name=_('UCI Code') )
	
	license_code = models.CharField( max_length=32, null=True, unique=True, verbose_name=_('License Code') )
				
	existing_bib = models.PositiveSmallIntegerField( null=True, blank=True, db_index=True, verbose_name=_('Existing Bib') )
	
	existing_tag = models.CharField( max_length=36, null=True, blank=True, unique=True, verbose_name=_('Existing Tag') )
	existing_tag2 = models.CharField( max_length=36, null=True, blank=True, unique=True, verbose_name=_('Existing Tag2') )
	
	suspended = models.BooleanField( default=False, verbose_name=_('Suspended'), db_index=True )
	active = models.BooleanField( default=True, verbose_name=_('Active'), db_index=True )

	SearchTextLength = 256
	search_text = models.CharField( max_length=SearchTextLength, blank=True, default='', db_index=True )

	def save( self, *args, **kwargs ):
		self.uci_code = (self.uci_code or '').strip().upper()
		if len(self.uci_code) == 3:
			self.uci_code += self.date_of_birth.strftime( '%Y%m%d' )
			
		for f in ['last_name', 'first_name', 'city', 'state_prov', 'nationality', 'uci_code']:
			setattr( self, f, (getattr(self, f) or '').strip() )
		
		if not self.uci_code and self.nationality:
			try:
				country = iso3166.countries.get( self.nationality )
				self.uci_code = '{}{}'.format( country.alpha3, self.date_of_birth.strftime('%Y%m%d') )
			except KeyError:
				pass
		
		for f in ['license_code', 'existing_tag', 'existing_tag2']:
			setattr( self, f, fixNullUpper(getattr(self, f)) )
			
		self.search_text = self.get_search_text()[:self.SearchTextLength]
		
		super(LicenseHolder, self).save( *args, **kwargs )

	def __unicode__( self ):
		return '%s, %s (%s, %s, %s, %s)' % (
			self.last_name.upper(), self.first_name,
			self.date_of_birth.isoformat(), self.get_gender_display(),
			self.uci_code, self.license_code
		)
		
	def full_name( self ):
		return "%s, %s" % (self.last_name.upper(), self.first_name)
		
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
		return getTagFormatStr( system_info.tag_template ).format( n=self.id )
		
	class Meta:
		verbose_name = _('LicenseHolder')
		verbose_name_plural = _('LicenseHolders')
		ordering = ['search_text']

class TeamHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	discipline = models.ForeignKey( 'Discipline', db_index = True )
	team = models.ForeignKey( 'Team', db_index = True )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def unicode( self ):
		return unicode(license_holder) + ' ' + unicode(discipline) + ' ' + unicode(team) + ' ' + unicode(effective_date)
	
	class Meta:
		verbose_name = _('TeamHint')
		verbose_name_plural = _('TeamHints')
		
class CategoryHint(models.Model):
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	discipline = models.ForeignKey( 'Discipline', db_index = True )
	category = models.ForeignKey( 'Category', db_index = True )
	effective_date = models.DateField( verbose_name = _('Effective Date'), db_index = True )
	
	def unicode( self ):
		return unicode(license_holder) + ' ' + unicode(discipline) + ' ' + unicode(category) + ' ' + unicode(effective_date)
	
	class Meta:
		verbose_name = _('CategoryHint')
		verbose_name_plural = _('CategoryHints')

class NumberSetEntry(models.Model):
	number_set = models.ForeignKey( 'NumberSet', db_index = True )
	license_holder = models.ForeignKey( 'LicenseHolder', db_index = True )
	bib = models.PositiveSmallIntegerField( db_index = True, verbose_name=_('Bib') )
	
	class Meta:
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
		_('Team'), _('Official'), _('Organizer')
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
			(199, _('Team Staff')),
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
			(320, _('Mechanic')),
			(330, _('Driver')),
			(399, _('Organizer Staff')),
			)
		),
	)
	role=models.PositiveSmallIntegerField(choices=COMPETITION_ROLE_CHOICES, default=110, verbose_name=_('Role') )
	
	preregistered=models.BooleanField( default=True, verbose_name=_('Preregistered') )
	
	registration_timestamp=models.DateTimeField( auto_now_add=True )
	category=models.ForeignKey( 'Category', null=True, blank=True, db_index=True )
	
	bib=models.PositiveSmallIntegerField( null=True, blank=True, db_index=True, verbose_name=_('Bib') )
	
	tag=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag') )
	tag2=models.CharField( max_length=36, null=True, blank=True, verbose_name=_('Tag2') )

	signature=models.TextField( blank=True, default='', verbose_name=_('Signature') )

	paid=models.BooleanField( default=False, verbose_name=_('Paid') )
	confirmed=models.BooleanField( default=False, verbose_name=_('Confirmed') )
	
	note=models.TextField( blank=True, default='', verbose_name=_('Note') )
	
	def save( self, *args, **kwargs ):
		competition = self.competition
		license_holder = self.license_holder
		
		for f in ['signature', 'note']:
			setattr( self, f, (getattr(self, f) or '').strip() )
		
		for f in ['tag', 'tag2']:
			setattr( self, f, fixNullUpper(getattr(self, f)) )
		
		if self.role == self.Competitor:
			if competition.number_set:
				if self.bib:
					try:
						nse = NumberSetEntry.objects.get( number_set=competition.number_set, license_holder=license_holder )
						if nse.bib != self.bib:
							nse.bib = self.bib
							nse.save()
					except NumberSetEntry.DoesNotExist:
						NumberSetEntry( number_set=competition.number_set, license_holder=license_holder, bib=self.bib ).save()
				else:
					NumberSetEntry.objects.filter( number_set=competition.number_set, license_holder=license_holder ).delete()
				
			if license_holder.existing_tag != self.tag or license_holder.existing_tag2 != self.tag2:
				license_holder.existing_tag = self.tag
				license_holder.existing_tag2 = self.tag2
				license_holder.save()
		
		super(Participant, self).save( *args, **kwargs )
	
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
	def role_full_name( self ):
		return u'{} {}'.format( self.ROLE_NAMES[self.roleCode()], get_role_display() )
	
	@property
	def needs_bib( self ):
		return self.role == 1 and not self.bib
	
	@property
	def needs_tag( self ):
		return self.competition.usingTags and not self.tag and not self.tag2
	
	@property
	def name( self ):
		fields = [ getattr(self.license_holder, a) for a in ['first_name', 'last_name', 'uci_code', 'license_code'] ]
		if self.team:
			fields.append( self.team.short_name() )
		return u''.join( [u'{} '.format(self.bib) if self.bib else u'', u', '.join( [f for f in fields if f] )] )
			
	def __unicode__( self ):
		return self.name
	
	def init_default_values( self ):
		if self.competition.number_set:
			try:
				self.bib = NumberSetEntry.objects.get( number_set=self.competition.number_set, license_holder=self.license_holder ).bib
			except NumberSetEntry.DoesNotExist:
				pass
		
		if self.competition.use_existing_tags:
			self.tag  = self.license_holder.existing_tag
			self.tag2 = self.license_holder.existing_tag2
	
		def init_values( pp ):
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
		for pp in Participant.objects.filter( license_holder=self.license_holder ).order_by( '-competition__start_date' ):
			if init_values(pp):
				init_date = pp.competition.start_date
				break
		#if not self.role:
		#	self.role = Participant._meta.get_field_by_name('role')[0].default
		
		try:
			th = TeamHint.objects.get( license_holder=self.license_holder, discipline=self.competition.discipline )
			if init_date is None or th.effective_date > init_date:
				init_date = th.effective_date
				self.team = th.team
		except TeamHint.DoesNotExist:
			pass
		
		self.role = Participant._meta.get_field_by_name('role')[0].default
		return self
	
	def get_bib_conflicts( self ):
		if not self.bib:
			return []
		q = Q( competition = self.competition ) & Q( bib = self.bib )
		category_numbers = self.competition.get_category_numbers( self.category ) if self.category else None
		if category_numbers:
			q &= Q( category__in = category_numbers.categories.all() )
		return list( p for p in Participant.objects.filter(q) if p != self )
	
	def get_start_waves( self ):
		if not self.category:
			return []
		return sorted( Wave.objects.filter(event__competition = self.competition, categories=self.category), key=Wave.get_start_time )
	
	def explain_integrity_error( self ):
		try:
			participant = Participant.objects.get(competition=self.competition, category=self.category, license_holder=self.license_holder)
			return True, _('This LicenseHolder is already in this Category'), participant
		except Participant.DoesNotExist:
			pass
			
		try:
			participant = Participant.objects.get(competition=self.competition, category=self.category, bib=self.bib)
			return True, _('A Participant is already in this Category with the same Bib.  Assign "No Bib" first, then try again.'), participant
		except Participant.DoesNotExist:
			pass
			
		try:
			participant = Participant.objects.get(competition=self.competition, category=self.category, tag=self.tag)
			return True, _('A Participant is already in this Category with the same Chip Tag.  Assign empty "Tag" first, and try again.'), participant
		except Participant.DoesNotExist:
			pass
			
		try:
			participant = Participant.objects.get(competition=self.competition, category=self.category, tag2=self.tag2)
			return True, _('A Participant is already in this Category with the same Chip Tag2.  Assign empty "Tag2" first, and try again.'), participant
		except Participant.DoesNotExist:
			pass
		
		return False, _('Unknown Integrity Error.'), None
	
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
		
# class EventTimeTrial( Event ):
	# penalties = generic.GenericRelation('Penalty')			# Required for each event subclass.
	# observations = generic.GenericRelation('Observation')	# Required for each event subclass.

	# # Time Trial fields
	# # Fields for assigning start times.
	# start_time = models.TimeField( null = True, blank = True )
	
	# first_participant_gap = models.PositiveSmallIntegerField(
						# choices=[(60*i, '%d min' % i) for i in xrange(1, 11)],
						# help_text = 'Time before first participant.',
						# default = 1*60 )
	# start_gap = models.PositiveSmallIntegerField(
						# choices=[(0,  '0 sec'),(30,  '30 sec')] + [(60*i, '%d min' % i) for i in xrange(1, 11)],
						# help_text = 'Gap between participant starts',
						# default = 1*60 )
	# heat_size = models.PositiveSmallIntegerField(
						# choices=[(i, '%d' % i) for i in xrange(1, 11)],
						# help_text = 'Number of participants started in each heat (usually 1)',
						# default = 1 )
	# wave_gap = models.PositiveSmallIntegerField(
						# choices=[(60*i, '%d min' % i) for i in xrange(5, 61, 5)],
						# help_text = 'Gap between start waves',
						# default = 5*60)
	# num_fastest_participants = models.PositiveSmallIntegerField(
						# choices=[(i, '%d' % i) for i in xrange(0, 16)],
						# help_text = 'Number of participants to get Fastest participants gap',
						# default = 5)
	# fastest_participants_gap = models.PositiveSmallIntegerField(
						# choices=[(60*i, '%d min' % i) for i in xrange(1, 11)],
						# help_text = 'Gap between fastest participants',
						# default = 2*60 )
	
	# # Registration and stopwatch control.
	# registration_status = models.CharField(max_length=1, choices=(('1', 'Open'), ('0', 'Closed')), default = '1')
	# stopwatch_start_time = DurationField( null = True, blank = True )

	# class Meta:
		# verbose_name = _('EventTimeTrial')
		# verbose_name_plural = _('EventTimeTrials')

# class PenaltyClass(models.Model):
	# name = models.CharField( max_length = 64 )
	# description = models.CharField( max_length = 80, default = '' )
		
	# class Meta:
		# verbose_name = _('PenaltyClass')
		# verbose_name_plural = _("PenaltyClasses")
		# ordering = ['name']

# class PenaltyTemplate(models.Model):
	# penalty_class = models.ForeignKey( PenaltyClass, db_index = True )
	# code = models.PositiveSmallIntegerField( db_index = True, default = 1 )
	
	# template_en = models.CharField( max_length = 160, default = '' )
	# template_fr = models.CharField( max_length = 160, default = '' )
	# template_es = models.CharField( max_length = 160, default = '' )
	
	# class Meta:
		# verbose_name = _('PenaltyTemplate')
		# verbose_name_plural = _("PenaltyTemplates")
		# ordering = ['code']

# class Penalty(models.Model):
	# competition = models.ForeignKey( Competition, db_index = True )
	
	# content_type = models.ForeignKey(ContentType)
	# object_id = models.PositiveIntegerField()
	# event = generic.GenericForeignKey('content_type', 'object_id')
	
	# PENALTY_TYPE_CHOICES = (
		# (1,	_('WARNING')),
		# (2,	_('FINE')),
		# (3,	_('RELEGATION')),
		# (4,	_('DISQUALIFICATION')),
	# )
	# penalty_type = models.PositiveSmallIntegerField(choices=PENALTY_TYPE_CHOICES, default = 1)
	
	# participant = models.ForeignKey( 'Participant', related_name='penalties' )
	# participant_victim = models.ForeignKey( 'Participant', null = True, related_name='victim_of_penalties' )
	
	# fine_amount = models.PositiveIntegerField( blank = True )
	# time_penalty = DurationField( blank = True )
	
	# distance = models.FloatField( default = 0.0, verbose_name = _('Distance') )
	# timestamp = models.DateTimeField( auto_now_add = True, verbose_name = _('Timestamp') )
	
	# description_en = models.CharField( max_length = 240, default = '' )
	# description_fr = models.CharField( max_length = 240, default = '' )
	# description_es = models.CharField( max_length = 240, default = '' )
	
	# class Meta:
		# verbose_name = _('Penalty')
		# verbose_name_plural = _("Penalties")
		# ordering = ['distance', 'penalty_type']

# #---------------------------------------------------------------------------------------------
	
# class EventEntry( models.Model ):
	# competition = models.ForeignKey( Competition, db_index = True )
	# participant = models.ForeignKey( 'Participant', db_index = True )
	
	# STATUS_CHOICES = (
		# (0, _('Finisher')),
		# (1, _('DNF')),
		# (2, _('PUL')),
		# (3, _('OTL')),
		# (4, _('DNS')),
		# (5, _('DQ')),			# Disqualified from this event.
		# (6, _('Eliminated')),	# Eliminated from the competition.
		# (7, _('NP')),
	# )
	# status = models.PositiveSmallIntegerField( choices=STATUS_CHOICES, default = 0 )
	
	# class Meta:
		# verbose_name = _("EventEntry")
		# verbose_name_plural = _("EventEntries")
		# abstract = True

# #---------------------------------------------------------------------------------------------

# class MassStartEntry( EventEntry ):
	# event = models.ForeignKey( "EventMassStart", db_index = True )
	# official_rank = models.PositiveSmallIntegerField( null = True, blank = True )
	# official_time = DurationField( null = True, blank = True )
	
	# laps_down = models.PositiveSmallIntegerField( null = True, blank = True, verbose_name = _('Laps Down') )
	
	# class Meta:
		# verbose_name = _('MassStartEntry')
		# verbose_name_plural = _('MassStartEntries')

# #---------------------------------------------------------------------------------------------

# class TimeTrialEntry( EventEntry ):
	# #--------------------------------------------------------------------------------------------
	# # Time Trial fields
	# #--------------------------------------------------------------------------------------------
	# event = models.ForeignKey( 'EventTimeTrial', db_index = True )
	
	# start_rank = models.PositiveSmallIntegerField( null = True, blank = True )
	# est_speed = models.FloatField()

	# WAVE_CHOICES = [(c, unicode(i+1)) for i, c in enumerate(u'123456789abcdef')]
	# start_wave = models.CharField(max_length = 1, choices = WAVE_CHOICES, default = '1' ) 
	
	# start_time = DurationField( null = True, blank = True )		# in race time, not clock time
	# finish_time = DurationField( null = True, blank = True )	# in race time, not clock time
	
	# observation = models.ForeignKey( 'Observation', null = True, on_delete = models.SET_NULL,
									# help_text="Observation for the Finish Time" )
	
	# start_time_early = DurationField( default = 0.0, help_text="Participant advantage for jumping start." )
	
	# adjustment_name_1 = models.CharField( max_length = 32, default = '', help_text="Adjustment Name" )
	# adjustment_time_1 = DurationField( default = 0.0, help_text="Time adjustment" )
	# adjustment_count_1 = models.PositiveSmallIntegerField( default = 0, help_text="Number of times to apply adjustment" )
	
	# adjustment_name_2 = models.CharField( max_length = 32, default = '', help_text="Adjustment Name" )
	# adjustment_time_2 = DurationField( default = 0.0, help_text="Time adjustment" )
	# adjustment_count_2 = models.PositiveSmallIntegerField( default = 0, help_text="Number of times to apply adjustment" )
	
	# def __unicode__( self ):
		# return '%d: %s' % (self.bib, self.participant.full_name())
	
	# @property
	# def time_delta( self ):
		# ''' Compute time without penalties. '''
		# try:
			# t = self.finish_time - self.start_time
			# if t.total_seconds() < 0:
				# return None
			# if self.start_time_early:
				# t += self.start_time_early
			# return t
		# except TypeError:
			# return None
	
	# @property
	# def ride_time( self ):
		# ''' Ride time reserved for finishers. '''
		# return self.time_delta if self.status == '0' else None
		
	# @property
	# def est_ride_time( self ):
		# return datetime.timedelta( seconds = (self.course.distance / self.est_speed) * (60.0 * 60.0) )
		
	# @property
	# def total_time_adjustments( self ):
		# t = None
		# if self.adjustment_time_1 and self.adjustment_count_1:
			# t = self.adjustment_time_1 * self.adjustment_count_1
			
		# if self.adjustment_time_2 and self.adjustment_count_2:
			# if not t:
				# t = self.adjustment_time_2 * self.adjustment_count_2
			# else:
				# t += self.adjustment_time_2 * self.adjustment_count_2
		# return t
	
	# @property
	# def final_time( self ):
		# ''' Compute time with penalties. '''
		# try:
			# t = self.ride_time
			# if self.adjustment_time_1 and self.adjustment_count_1:
				# t += self.adjustment_time_1 * self.adjustment_count_1
			# if self.adjustment_time_2 and self.adjustment_count_2:
				# t += self.adjustment_time_2 * self.adjustment_count_2
			# return t
		# except (AttributeError, TypeError, ValueError):
			# return None
			
	# class Meta:
		# verbose_name = _("TimeTrialEntry")
		# verbose_name_plural = _("TimeTrialEntries")

# #-------------------------------------------------------------------------------------

# class KOMPoints( models.Model ):
	# competition = models.ForeignKey( Competition, db_index = True )
	
	# content_type = models.ForeignKey(ContentType)
	# object_id = models.PositiveIntegerField()
	# event = generic.GenericForeignKey('content_type', 'object_id')
	
	# name = models.CharField( max_length = 64 )
	# description = models.CharField( max_length = 80, default = '' )
	
	# distance = models.FloatField()
	
	# class Meta:
		# verbose_name = _("KOMPoints")
		# verbose_name_plural = _("KOMPoints")
		# ordering = ['distance']
	
# class KOMPointsResult( models.Model ):
	# kom = models.ForeignKey( KOMPoints )
	
	# points = models.PositiveSmallIntegerField( default = 5 )
	# participant = models.ForeignKey( Participant, blank = True )
	
	# class Meta:
		# verbose_name = _("KOMPointsResult")
		# verbose_name_plural = _("KOMPointsResult")
		# ordering = ['-points']
		
# #-------------------------------------------------------------------------------------

# class SprintPoints( models.Model ):
	# competition = models.ForeignKey( Competition, db_index = True )
	
	# content_type = models.ForeignKey(ContentType)
	# object_id = models.PositiveIntegerField()
	# event = generic.GenericForeignKey('content_type', 'object_id')
	
	# name = models.CharField( max_length = 64 )
	# description = models.CharField( max_length = 80, default = '' )
	
	# distance = models.FloatField()
	
	# class Meta:
		# verbose_name = _("SprintPoints")
		# verbose_name_plural = _("SprintPoints")
		# ordering = ['distance']
	
# class SprintPointsResult( models.Model ):
	# race_sprint = models.ForeignKey( SprintPoints )
	
	# points = models.PositiveSmallIntegerField( default = 5 )
	# participant = models.ForeignKey( Participant, blank = True )
	
	# class Meta:
		# verbose_name = _("SprintPointsResult")
		# verbose_name_plural = _("SprintPointsResults")
		# ordering = ['-points']

# #-------------------------------------------------------------------------------------

# class TimeBonus( models.Model ):
	# competition = models.ForeignKey( Competition, db_index = True )
	
	# content_type = models.ForeignKey(ContentType)
	# object_id = models.PositiveIntegerField()
	# event = generic.GenericForeignKey('content_type', 'object_id')
	
	# name = models.CharField( max_length = 64 )
	# description = models.CharField( max_length = 80, default = '' )
	
	# distance = models.FloatField()
	
	# class Meta:
		# verbose_name = _('TimeBonus')
		# verbose_name_plural = _("TimeBonuses")
		# ordering = ['distance']
	
# class TimeBonusResult( models.Model ):
	# time_bonus = models.ForeignKey( TimeBonus )
	
	# time_granted = DurationField()
	# participant = models.ForeignKey( Participant, blank = True )
	
	# class Meta:
		# verbose_name = _('TimeBonusResult')
		# verbose_name_plural = _("TimeBonuseResults")
		# ordering = ['-time_granted']

# #-------------------------------------------------------------------------------------

# class Observation( models.Model ):
	# content_type = models.ForeignKey(ContentType)
	# object_id = models.PositiveIntegerField()
	# event = generic.GenericForeignKey('content_type', 'object_id')
	
	# bib = models.PositiveSmallIntegerField()
	# OBSERVATION_TYPE_CHOICES = (
		# (0, _('FinishLine')),
		# (1, _('Turnaround')),
		# (2, _('Checkpoint')),
		# (3, _('Crash')),
		# (4, _('Mechanical')),
	# )
	# observation_type = models.PositiveSmallIntegerField( choices=OBSERVATION_TYPE_CHOICES, default = 0 )
	
	# distance = models.FloatField( null = True, blank = True )
	# race_time = DurationField( null = True, blank = True )
	
	# note = models.CharField( blank = True, default = '', max_length = 256 )
	
	# active = models.BooleanField( default = True )
	
	# class Meta:
		# verbose_name = _('Observation')
		# verbose_name_plural = _("Observations")
		# ordering = ['distance', 'race_time']
	
#-------------------------------------------------------------------------------------
# class Series( models.Model ):
	# name = models.CharField( max_length = 80, help_text='Name of the Series' )
	# organizer = models.CharField( max_length = 80, default = '', help_text='Organizer of the Series' )
	
	# category_format = models.ForeignKey( 'CategoryFormat', help_text='Format used for Participant Categories in each event.' )
	
	# SERIES_RANKING_CHOICES = (
		# ('P',	'Total Points'),
		# ('A',	'Average of Best Speeds'),
	# )
	# ranking_policy = models.CharField( max_length = 1, choices=make_choices(SERIES_RANKING_CHOICES), default = 'P', help_text='Policy used to combine results from events.' )
	
	# points_for_1  = models.PositiveSmallIntegerField( default = 25 )
	# points_for_2  = models.PositiveSmallIntegerField( default = 24 )
	# points_for_3  = models.PositiveSmallIntegerField( default = 23 )
	# points_for_4  = models.PositiveSmallIntegerField( default = 22 )
	# points_for_5  = models.PositiveSmallIntegerField( default = 21 )
	# points_for_6  = models.PositiveSmallIntegerField( default = 20 )
	# points_for_7  = models.PositiveSmallIntegerField( default = 19 )
	# points_for_8  = models.PositiveSmallIntegerField( default = 18 )
	# points_for_9  = models.PositiveSmallIntegerField( default = 17 )
	# points_for_10 = models.PositiveSmallIntegerField( default = 16 )
	# points_for_11 = models.PositiveSmallIntegerField( default = 15 )
	# points_for_12 = models.PositiveSmallIntegerField( default = 14 )
	# points_for_13 = models.PositiveSmallIntegerField( default = 13 )
	# points_for_14 = models.PositiveSmallIntegerField( default = 12 )
	# points_for_15 = models.PositiveSmallIntegerField( default = 11 )
	# points_for_16 = models.PositiveSmallIntegerField( default = 10 )
	# points_for_17 = models.PositiveSmallIntegerField( default =  9 )
	# points_for_18 = models.PositiveSmallIntegerField( default =  8 )
	# points_for_19 = models.PositiveSmallIntegerField( default =  7 )
	# points_for_20 = models.PositiveSmallIntegerField( default =  6 )
	# points_for_21 = models.PositiveSmallIntegerField( default =  5 )
	# points_for_22 = models.PositiveSmallIntegerField( default =  4 )
	# points_for_23 = models.PositiveSmallIntegerField( default =  3 )
	# points_for_24 = models.PositiveSmallIntegerField( default =  2 )
	# points_for_25 = models.PositiveSmallIntegerField( default =  1 )
	
	# points_for_participation = models.PositiveSmallIntegerField( default = 1, help_text='Points awarded for participating' )
	# number_of_best_events_for_points = models.PositiveSmallIntegerField( default = 5, help_text='Number of best points to use for Total Points.' )
	# TIE_BREAKING_RULE = (
		# ('R',	'Most recent event'),
		# ('W',	'Most wins over other participant'),
	# )
	# tie_breaking_rule = models.CharField( max_length = 1, choices=make_choices(TIE_BREAKING_RULE), default = 'R', help_text='Rule to break ties for same number of points.' )
	
# -------------------------------------------------------------------------------------------------
	
	# number_of_best_events_for_average = models.PositiveSmallIntegerField( default = 5, help_text='Number of best times to use for Average Speed.' )
	
	# def full_name( self ):
		# return self.name + ', ' + self.organizer
	
	# def __unicode__( self ):
		# return self.name
	
	# class Meta:
		# verbose_name = _("Series")
		# verbose_name_plural = _("Series")
