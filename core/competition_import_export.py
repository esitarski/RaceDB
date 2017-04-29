from __future__ import unicode_literals

import json
import datetime
from collections import defaultdict, deque

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.serializers import base
from django.db import DEFAULT_DB_ALIAS, models
from django.utils import six
from django.utils.encoding import force_text
from django.db import transaction

from utils import get_search_text, removeDiacritic
from get_id import get_id

from models import *

def merge( *args ):
	merged = {}
	for v in args:
		merged.update( v )
	return merged

class processing_status( object ):
	def __init__( self, instance_total ):
		self.reset( instance_total )
	
	def reset( self, instance_total ):
		self.instance_count = 0
		self.instance_total = max( instance_total, 1 )
		self.t_last = self.t_start = datetime.datetime.now()
		self.update_frequency = 500
		
	def inc( self, model_name ):
		self.instance_count += 1
		if self.instance_count % self.update_frequency == 0:
			t_cur = datetime.datetime.now()
			rate = self.update_frequency / ((t_cur - self.t_last).total_seconds() + 0.000001 )
			ave_rate = self.instance_count / ((t_cur - self.t_start).total_seconds() + 0.000001 )
			
			s_remaining = (self.instance_total - self.instance_count) / ave_rate
			print '{:4.1f}%   {:7.1f} objs/sec   {:4.0f} secs  {:4.0f} est secs remaining ({})...'.format(
				(100.0*self.instance_count)/self.instance_total,
				rate,
				(t_cur - self.t_start).total_seconds(),
				s_remaining,
				model_name,
			)
			self.t_last = t_cur
			
def get_key( Model, pk ):
	return Model._meta.db_table, int(pk)

class transaction_save( object ):
	MaxTransactionRecords = 999
	def __init__( self, old_new ):
		self.model = None
		self.old_new = old_new
		self.pending = []
		
	def save( self, model, db_object, instance, pk_old ):
		if model != self.model:
			self.flush()
			self.model = model
			
		self.pending.append( (db_object, instance, pk_old) )
		if len(self.pending) >= self.MaxTransactionRecords:
			self.flush()
		
	def flush( self, model=None ):
		if model != self.model and self.pending:
			for i in xrange(0, len(self.pending), self.MaxTransactionRecords):
				with transaction.atomic():
					for dbo, inst, pko in self.pending[i:i+self.MaxTransactionRecords]:
						dbo.save()
						self.old_new[get_key(self.model, pko)] = inst.pk
			del self.pending[:]
			
processing = processing_status( 1 )
def _build_instance(Model, data, db, field_names, existing_license_codes, existing_tags, system_info):
	"""
	Build a model instance.
	Attempt to find an existing database record based on existing related fields as well as important data fields.
	Returns new instance and a flag, True if an update to an existing record, False if this is a new record.
	"""
	
	processing.inc(Model.__name__)
	
	instance = Model( **data )
	existing_instance = None
	
	# Add the references to the search.
	included_search_fields = {}
	for field_name in field_names:
		field = Model._meta.get_field(field_name)
		if (field.many_to_one or field.one_to_one) and data.get(field_name+'_id', None) is not None:
			included_search_fields[field_name+'__id'] = data[field_name+'_id']
	
	def search( **kwargs ):
		return Model.objects.filter( **merge(included_search_fields, kwargs) ).first()
	
	def has_data_fields( *args ):
		return all( field_name in field_names and not Model._meta.get_field(field_name).remote_field for field_name in args )
	
	if Model == LicenseHolder:
		'''
		if instance.last_name.upper() == 'KOHNEN' and instance.first_name == 'Courtney':
			import pdb; pdb.set_trace()
			pass
		'''
			
		# Search by UCIID (guaranteed unique).
		if instance.uci_id:
			existing_instance = search( uci_id=instance.uci_id )
		
		# If no match, search by license_code, or (last, first, gender, DOB) depending on configuration.
		if not existing_instance:
			if system_info.license_holder_unique_by_license_code:
				if instance.license_code:
					existing_instance = search( license_code=instance.license_code )
			else:			
				existing_instance = search(
					search_text__startswith=get_search_text([instance.last_name, instance.first_name]),
					gender=instance.gender,
					date_of_birth=instance.date_of_birth,
				)
			
		#---------------------------------------------------------------
		# License logic.
		#
		if existing_instance:
			# Use this database's version of the license code if none given.
			if not instance.license_code:
				instance.license_code = existing_instance.license_code
			
			elif instance.license_code != existing_instance.license_code:
				existing_license_codes.discard( existing_instance.license_code )
				
				# If the license causes a conflict, create a unique one.
				while instance.license_code in existing_license_codes:
					instance.license_code = random_temp_license()
				existing_instance.license_code = instance.license_code
				existing_license_codes.add( instance.license_code )
		else:
			# No existing instance - create a random one.
			while not instance.license_code or instance.license_code in existing_license_codes:
				instance.license_code = random_temp_license()			
			existing_license_codes.add( instance.license_code )
			
		#---------------------------------------------------------------
		# Tag logic.
		#
		if existing_instance:
			if not instance.existing_tag:
				# Re-use the existing tag if one is not provided.
				instance.existing_tag = existing_instance.existing_tag
			
			elif instance.existing_tag != existing_instance.existing_tag:
				existing_tags.discard( existing_instance.existing_tag )
				
				# If the new tag causes a conflict, create a unique one.
				while instance.existing_tag in existing_tags:
					instance.existing_tag = get_id( system_info.tag_bits )				
				existing_tags.add( instance.existing_tag )
		else:
			if instance.existing_tag:
				while instance.existing_tag in existing_tags:
					instance.existing_tag = get_id( system_info.tag_bits )
				existing_tags.add( instance.existing_tag )
		
	elif Model == Category:
		existing_instance = search( code=instance.code, gender=instance.gender, )
	
	elif Model == NumberSetEntry:
		existing_instance = search( bib=instance.bib, date_lost=instance.date_lost )
	
	elif Model == CategoryNumbers:
		# This works because the CategoryNumbers categories list is exclusive between CategoryNumbers records.
		existing_instance = search( range_str=instance.range_str, categories__in=data.get('categories',[]) )
	
	elif Model == UpdateLog:
		existing_instance = search( created=instance.created )
	
	elif has_data_fields('name'):
		
		included_search_fields['name'] = instance.name
		if has_data_fields('team_type'):	# Teams
			existing_instance = search( team_type=instance.team_type, )
		elif has_data_fields('date_time'):	# EventMassStart, EventTT
			existing_instance = search( date_time=instance.date_time )
		elif has_data_fields('start_date'):	# Competition
			existing_instance = search( start_date=instance.start_date )	
		else:
			existing_instance = search()
	
	else:
		existing_instance = search()
	
	instance.pk = existing_instance.pk if existing_instance else None
	return instance, existing_instance

def instance_changed( instance, existing_instance ):
	if not existing_instance:
		return True
	return instance.__dict__ != existing_instance.__dict__

def competition_deserializer( object_list, **options ):
	"""
	Deserialize complex Python objects back into Django ORM instances.

	It's expected that you pass the Python objects themselves (instead of a
	stream or a string) to the constructor
	
	Links between objects are patched to newly created instances,
	or existing records in the database.
	"""
	processing.reset( len(object_list) )
	
	db = options.pop('using', DEFAULT_DB_ALIAS)
	field_names_cache = {}  # Model: <list of field_names>
	
	object_list = deque( object_list )
	
	system_info = SystemInfo.get_singleton()
	
	existing_number_sets = set()
	
	dependencies = defaultdict( list )	# Place to hold objects when waiting for referenced objects to load.
	old_new = {}
	
	existing_license_codes = set( LicenseHolder.objects.all().values_list('license_code',flat=True) )
	existing_tags = set( LicenseHolder.objects.all().values_list('existing_tag',flat=True) )
	existing_license_holder_category = set()
	more_recently_updated_license_holders = None
	
	ts = transaction_save( old_new )
	while object_list:
		d = object_list.popleft()

		# Look up the model and starting build a dict of data for it.
		Model = _get_model(d["model"])
		ts.flush( Model )
		
		data = {}
		if 'pk' in d:
			try:
				data[Model._meta.pk.attname] = Model._meta.pk.to_python(d.get('pk'))
			except Exception as e:
				raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), None)
		
		m2m_data = {}
		pk_old = int(d['pk'])

		try:
			field_names = field_names_cache[Model]
		except KeyError:
			field_names = field_names_cache[Model] = {f.name for f in Model._meta.get_fields()}

		# Handle each field
		has_dependency = False
		for (field_name, field_value) in six.iteritems(d["fields"]):

			if has_dependency:
				break
			
			if field_name not in field_names:
				# skip fields no longer on model
				continue

			if isinstance(field_value, str):
				field_value = force_text(
					field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True
				)

			field = Model._meta.get_field(field_name)

			# Handle M2M relations
			if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
				model = field.remote_field.model
				def m2m_convert(v):
					return force_text(model._meta.pk.to_python(v), strings_only=True)

				try:
					m2m_data[field.name] = []
					for pk in field_value:
						m2m_data[field.name].append(m2m_convert(pk))
						key = get_key(model, m2m_data[field.name][-1])
						try:
							m2m_data[field.name][-1] = old_new[key]
						except KeyError:
							dependencies[key].append( d )
							has_dependency = True
							break
				
				except Exception as e:
					raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), pk)

			# Handle FK fields
			elif field.remote_field and isinstance(field.remote_field, models.ManyToOneRel):
				model = field.remote_field.model
				if field_value is not None:
					try:
						default_manager = model._default_manager
						field_name = field.remote_field.field_name
						data[field.attname] = model._meta.get_field(field_name).to_python(field_value)
						try:
							data[field.attname] = old_new[get_key(model, data[field.attname])]
						except KeyError:
							dependencies[get_key(model, data[field.attname])].append( d )
							has_dependency = True

					except Exception as e:
						raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)
				else:
					data[field.attname] = None

			# Handle all other fields
			else:
				try:
					data[field.name] = field.to_python(field_value)
				except Exception as e:
					raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)

		if not has_dependency:
			instance, existing_instance = _build_instance(
				Model, data, db, field_names, existing_license_codes, existing_tags, system_info
			)
			if Model == Competition:
				competition = instance
				more_recently_updated_license_holders = set(
					Participant.objects.filter(competition__start_date__gt=competition.start_date)
					.values_list('license_holder__id',flat=True)
				)
				existing_license_holder_category = set( tuple(lh_cat)
					for lh_cat in Participant.objects.filter(competition=competition).values_list('license_holder', 'category') )
			
			db_object = base.DeserializedObject(instance, m2m_data)
			if existing_instance:	# This is an update as there is an existing instance.
				# Check whether the existing record is more recent and should not be preserved.
				if Model == LicenseHolder:
					if not more_recently_updated_license_holders or instance.id not in more_recently_updated_license_holders:
						ts.save( Model, db_object, instance, pk_old )
				elif Model == Waiver:
					if instance.date_signed > existing_instance.date_signed:
						ts.save( Model, db_object, instance, pk_old )
				elif Model == LegalEntity:
					existing_legal_entity = LegalEntity.objects.get(id=instance.id)
					if instance.waiver_expiry_date > existing_legal_entity.waiver_expiry_date:
						ts.save( Model, db_object, instance, pk_old )
				elif Model == NumberSet:
					# Keep track of this number set if it is new.  A new number set means that we do not have to compute
					# any incremental update, which is much faster.
					existing_number_sets.add( existing_instance.id )
					ts.save( Model, db_object, instance, pk_old )
				elif Model == NumberSetEntry:
					if not more_recently_updated_license_holders or instance.id not in more_recently_updated_license_holders:
						if instance.date_lost:
							if instance.date_lost != existing_instance.date_lost:
								existing_instance.number_set.set_lost(instance.license_holder, instance.bib, instance.date_lost)
						else:
							if existing_instance.bib != instance.bib:
								existing_instance.number_set.assign_bib(instance.license_holder, instance.bib)
				else:
					ts.save( Model, db_object, instance, pk_old )
			else:
				if Model == NumberSetEntry and instance.number_set_id in existing_number_sets:
					ns = instance.number_set
					if instance.date_lost:
						ns.set_lost(instance.bib, instance.license_holder, instance.date_lost)
					else:
						ns.assign_bib(instance.license_holder, instance.bib)
				elif Model == Participant:
					lh_cat = (instance.license_holder_id, instance.category_id if instance.category else None)
					if lh_cat in existing_license_holder_category:
						print '****Duplicate Participant LicenseHolder Category Integrity Error.  Skipped.'
						lh = instance.license_holder
						print removeDiacritic(u'    {},{} {}'.format(lh.last_name, lh.first_name, lh.license_code) )
					else:
						existing_license_holder_category.add( lh_cat )
						ts.save( Model, db_object, instance, pk_old )
				else:
					ts.save( Model, db_object, instance, pk_old )
			
			key = get_key(Model, pk_old)
			object_list.extend( dependencies.pop(key, []) )
			if instance.pk:
				old_new[key] = instance.pk
			
	ts.flush()

def _get_model(model_identifier):
    """
    Helper to look up a model from an "app_label.model_name" string.
    """
    try:
        return apps.get_model(model_identifier)
    except (LookupError, TypeError):
        raise base.DeserializationError("Invalid model identifier: '%s'" % model_identifier)

def competition_import( stream=None, pydata=None ):
	competition_deserializer( pydata if pydata else json.load(stream) )

def get_competition_name_start_date( stream=None, pydata=[],
		import_as_template=None, name=None, start_date=None ):
	if stream:
		pydata = json.load( stream )
	
	if import_as_template:
		pydata = [d for d in pydata if not (d['model'] in ('core.licenceholder' or 'core.team') or 'license_holder' in d['fields'] or 'participant' in d['fields']) ]
			
	for d in pydata:
		if d['model'] == 'core.competition':
			if name:
				d['fields']['name'] = name
			
			if start_date:
				dt_comp = datetime.date( *[int(v) for v in d['fields']['start_date'].split('-')] )
				dt_delta = start_date - dt_comp
				for d_event in pydata:
					if d_event['model'] not in ('core.eventmassstart', 'core.eventtt'):
						continue
					dt_event = datetime.date( *[int(v) for v in d_event['fields']['date_time'][:10].split('-')] ) + dt_delta
					d_event['fields']['date_time'] = dt_event.strftime('%Y-%m-%d') + d_event['fields']['date_time'][10:]
				
				d['fields']['start_date'] = start_date.strftime('%Y-%m-%d')
			
			return d['fields']['name'], datetime.date( *[int(v) for v in d['fields']['start_date'].split('-')] ), pydata
	
	return None, None, None

# ----------------------------------------------------------------------------------------------------

def competition_export( competition, stream, export_as_template=False, remove_ftp_info=False ):
	if remove_ftp_info:
		attrs = ("ftp_host", "ftp_user", "ftp_password", "ftp_path", "ftp_upload_during_race", "ga_tracking_id")
		ftp_info_save = { a:getattr(competition, a) for a in attrs }
		for a in attrs:
			setattr( competition, a, Competition._meta.get_field(a).default )
  
	def get_participants():
		return competition.get_participants()
	
	license_holder_query = LicenseHolder.objects.filter( pk__in=get_participants().values_list('license_holder',flat=True).distinct() )
	
	def get_teams():
		return Team.objects.filter( pk__in=get_participants().exclude(team__isnull=True).values_list('team',flat=True).distinct() )
	
	arr = []
	arr.extend( competition.report_labels.all() )
	arr.extend( v for v in (
		competition.category_format,
		competition.discipline,
		competition.race_class,
		competition.legal_entity,
		competition.number_set,
		competition.seasons_pass) if v
	)
	
	arr.append( competition )
	arr.extend( competition.category_format.category_set.all() )
	if not export_as_template:
		arr.extend( get_teams() )
		arr.extend( license_holder_query )
		# List the participants in most complete sequence.
		# This helps do the right thing in import if there are license holder duplicates.
		arr.extend( get_participants().filter( Q(bib__isnull=False) & Q(category__isnull=False) ) )
		arr.extend( get_participants().filter( Q(bib__isnull=True)  & Q(category__isnull=False) ) )
		arr.extend( get_participants().filter( Q(bib__isnull=False) & Q(category__isnull=True)  ) )
		arr.extend( get_participants().filter( Q(bib__isnull=True)  & Q(category__isnull=True)  ) )
	
		if competition.number_set:
			arr.extend( competition.number_set.numbersetentry_set.filter(license_holder__in=license_holder_query) )
		if competition.seasons_pass:
			arr.extend( competition.seasons_pass.seasonspassholder_set.filter(license_holder__in=license_holder_query) )
		if competition.legal_entity:
			arr.extend( competition.legal_entity.waiver_set.filter(license_holder__in=license_holder_query) )
				
		arr.extend( UpdateLog.objects.filter(
				created__gte=competition.start_date - datetime.timedelta(days=14),
				created__lte=competition.start_date + datetime.timedelta(days=14)
			)
		)
	
	arr.extend( competition.categorynumbers_set.all() )
	
	#-------------------------------------------------------------------
	arr.extend( competition.eventmassstart_set.all() )
	arr.extend( Wave.objects.filter(event__competition=competition) )
	if not export_as_template:
		arr.extend( ResultMassStart.objects.filter(event__competition=competition) )
		arr.extend( RaceTimeMassStart.objects.filter(result__event__competition=competition) )
	
	#-------------------------------------------------------------------
	arr.extend( competition.eventtt_set.all() )
	arr.extend( WaveTT.objects.filter(event__competition=competition) )	
	if not export_as_template:
		arr.extend( EntryTT.objects.filter(event__competition=competition) )
		arr.extend( ResultTT.objects.filter(event__competition=competition) )
		arr.extend( RaceTimeTT.objects.filter(result__event__competition=competition) )
	
	#-------------------------------------------------------------------
	if not export_as_template:
		arr.extend( competition.participantoption_set.all() )
		
	if export_as_template:
		# Clear any references to participant-specific data.
		arr = [o for o in arr if not (
			hasattr(o, 'license_holder') or
			hasattr(o, 'participant') or
			hasattr(o, 'result') or
			isinstance(o, LicenseHolder) or
			isinstance(o, Team))
		]
	
	# Serialize all the objects to json.
	json_serializer = serializers.get_serializer("json")()
	json_serializer.serialize(arr, indent=0, stream=stream)

	if remove_ftp_info:
		for k, v in ftp_info_save.iteritems():
			setattr( competition, k, v )

	return arr

#-----------------------------------------------------------------------

def license_holder_export( stream ):
	arr = []
	
	update_category_hints()
	arr.extend( Discipline.objects.filter( pk__in=CategoryHint.objects.all().values_list('discipline',flat=True).distinct() ) )
	for category_format in CategoryFormat.objects.filter( pk__in=CategoryHint.objects.all().values_list('category__format',flat=True).distinct() ):
		arr.append( category_format )
		arr.extend( category_format.category_set.all() )
	
	update_team_hints()
	arr.extend( Team.objects.filter( pk__in=TeamHint.objects.all().values_list('team',flat=True).distinct() ) )
	arr.extend( LicenseHolder.objects.all() )
	arr.extend( TeamHint.objects.all() )
	arr.extend( CategoryHint.objects.all() )
	
	for ns in NumberSet.objects.all():
		arr.append( ns )
		arr.extend( ns.numbersetentry_set.all() )
	for sp in SeasonsPass.objects.all():
		arr.append( sp )
		arr.extend( sp.seasonspassholder_set.all() )
	for le in LegalEntity.objects.all():
		arr.append( le )
		arr.extend( le.waiver_set.all() )
		
	# Serialize all the objects to json.
	json_serializer = serializers.get_serializer("json")()
	json_serializer.serialize(arr, indent=0, stream=stream)

	return arr

license_holder_import = competition_import
