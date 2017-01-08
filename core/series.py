import operator
from collections import defaultdict

from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.forms import formset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

ItemsPerPage = 25
def getPaginator( request, page_key, items ):
	paginator = Paginator( items, ItemsPerPage )
	page = request.GET.get('page',None) or request.session.get(page_key,None)
	try:
		items = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		page = 1
		items = paginator.page(page)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		page = paginator.num_pages
		items = paginator.page(page)
	request.session[page_key] = page
	return items, paginator

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesList( request, moveDirection=None, seriesId=None ):
	series = Series.objects.first()
	if series:
		series.normalize()
		
	if moveDirection is not None:
		moveDirection = int(moveDirection) - 100
		series = get_object_or_404( Series, pk=seriesId )
		series.move( moveDirection )
	
	series = Series.objects.all()
	return render( request, 'series_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesNew( request, categoryFormatId=None ):
	if categoryFormatId is None:
		category_formats = CategoryFormat.objects.all()
		return render( request, 'series_category_format_select.html', locals() )
	
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )
	series = Series( name=timezone.now().strftime("SeriesNew %H:%M:%S"), category_format=category_format )
	series.save()
	series.move_to( 0 )
	
	return HttpResponseRedirect(getContext(request,'cancelUrl') + 'SeriesEdit/{}/'.format(series.id) )

@autostrip
class SeriesForm( ModelForm ):
	class Meta:
		model = Series
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(SeriesForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('name', size=20),
				Field('description', size=40),
			),
			Row(
				Field('ranking_criteria'),
				Field('best_results_to_consider'),
				Field('must_have_completed'),
			),
			Row(
				HTML( '<strong>' ), HTML( _('Break Ties as follows:') ), HTML( '</strong>' ),
			),
			Row(
				Field('consider_most_events_completed'),
				HTML('&nbsp;'*6 + '<strong>' ), HTML( _('then consider') ), HTML( '</strong>' + '&nbsp;'*6),
				Field('tie_breaking_rule'),
			),
			Row(
				HTML( _('Finally, break remaining ties with the most recent result.') ),
			),
			Row(
				Field('show_last_to_first'),
			),
			Field('category_format', type='hidden'),
			Field('sequence', type='hidden'),
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesEdit( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	if not series.seriesincludecategory_set.exists():
		for category in series.category_format.category_set.all():
			SeriesIncludeCategory( series=series, category=category ).save()
	if series.ranking_criteria == 0 and not series.seriespointsstructure_set.exists():
		SeriesPointsStructure( series=series ).save()
		
	included_categories = [ic.category for ic in series.seriesincludecategory_set.all()]
	excluded_categories = series.category_format.category_set.exclude( pk__in=[c.pk for c in included_categories] )

	ces = list( series.seriescompetitionevent_set.all() )
	competitions = defaultdict( list )
	for ce in ces:
		competitions[ce.event.competition].append( ce )
	competitions = [(c, ces) for c, ces in competitions.iteritems()]
	competitions.sort( key=lambda ce: ce[0].start_date, reverse=True )
	for c, ces in competitions:
		ces.sort( key=lambda ce:ce.event.date_time )

	return GenericEdit( Series, request, series.id, SeriesForm, 'series_form.html', locals() )


@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesDetailEdit( request, seriesId ):
	return GenericEdit( Series, request, seriesId, SeriesForm, 'generic_form.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesDelete( request, seriesId, confirmed=0 ):
	series = get_object_or_404( Series, pk=seriesId )
	if int(confirmed):
		series.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Delete: '), series.name, u', ', series.description )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------

class EventSelectForm( Form ):
	events = forms.MultipleChoiceField( label=_("Events to include from the Competition"), help_text=_('Ctrl-Click to Multi-select') )
	
	def __init__( self, *args, **kwargs ):
		series = kwargs.pop( 'series' )
		competition = kwargs.pop( 'competition' )
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(EventSelectForm, self).__init__(*args, **kwargs)
		
		category_pk = set( series.get_category_pk() )
		events = [e for e in competition.get_events() if not set(c.pk for c in e.get_categories()).isdisjoint(category_pk)]
		events.sort( key=operator.attrgetter('date_time') )
		self.fields['events'].choices = [('{}-{}'.format(e.event_type,e.id), string_concat(e.date_time.strftime('%Y-%m-%d %H:%M'), u': ', e.name)) for e in events]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('events', size=30),
			)
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCompetitionAdd( request, seriesId, competitionId=None ):
	page_key = 'series_competition_add_page'
	series = get_object_or_404( Series, pk=seriesId )
	if competitionId is not None:
		competition = get_object_or_404( Competition, pk=competitionId )
		
		series.remove_competition( competition )
		default_points_structure = series.get_default_points_structure()
		category_pk = set( series.get_category_pk() )
		for e in competition.get_events():
			if not set(c.pk for c in e.get_categories()).isdisjoint(category_pk):
				sce = SeriesCompetitionEvent( series=series, points_structure=default_points_structure )
				sce.event = e
				sce.save()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
				
	existing_competition_pk = set( ce.event.competition.pk for ce in series.seriescompetitionevent_set.all() )
	competitions = Competition.objects.filter( category_format=series.category_format ).exclude( pk__in=existing_competition_pk ).order_by('-start_date')
	competitions, paginator = getPaginator( request, page_key, competitions )
	return render( request, 'series_competitions_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCompetitionRemove( request, seriesId, competitionId, comfirmed=0 ):
	series = get_object_or_404( Series, pk=seriesId )
	competition = get_object_or_404( Competition, pk=competitionId )
	if int(confirmed):
		series.remove_competition( competition )
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Remove: '), competition.date_range_year_str, u': ', competition.name )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

def GetEventForm( series ):
	class EventForm( Form ):
		select = forms.BooleanField( required=False )
		name = forms.CharField( widget = forms.HiddenInput(), required=False )
		options = { 'choices':[(ps.pk, ps.name) for ps in series.seriespointsstructure_set.all()] }
		if series.ranking_criteria != 0:
			options['widget'] = forms.HiddenInput()
		points_structure = forms.ChoiceField( **options )
		et = forms.IntegerField( widget = forms.HiddenInput(), required=False )
		pk = forms.IntegerField( widget = forms.HiddenInput(), required=False )
		
		def __init__( self, *args, **kwargs ):
			super( EventForm, self ).__init__( *args, **kwargs )
			initial = kwargs.get( 'initial', {} )
			if initial:
				self.fields['label'] = initial['name']
		
	return EventForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCompetitionEdit( request, seriesId, competitionId ):
	series = get_object_or_404( Series, pk=seriesId )
	competition = get_object_or_404( Competition, pk=competitionId )
	
	default_ps = series.get_default_points_structure().pk
	EventFormSet = formset_factory(GetEventForm(series), extra=0)
	
	def get_form_set():
		category_pk = set( series.get_category_pk() )
		events = [e for e in competition.get_events() if not set(c.pk for c in e.get_categories()).isdisjoint(category_pk)] 
		events.sort( key=operator.attrgetter('date_time') )

		events_included = set( series.get_events_for_competition(competition) )
		points_structure = {ce.event:ce.points_structure.pk for ce in series.seriescompetitionevent_set.all() if ce.event.competition == competition}
		
		print [e.pk for e in events]
		
		initial = [{
			'select': e in events_included,
			'name': e.date_time.strftime('%a %H:%M') + ': ' + e.name,
			'points_structure': points_structure.get(e, default_ps),
			'et': e.event_type,
			'pk': e.pk,
		} for e in events]
		print initial
		return EventFormSet( initial=initial )

	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form_set = EventFormSet( request.POST )
		if form_set.is_valid():

			event_points = []
			for f in form_set:
				fields = f.cleaned_data
				if not fields['select']:
					continue
				
				e = (EventMassStart, EventTT)[fields['et']].objects.get( pk=fields['pk'] )
				ps = SeriesPointsStructure.objects.get( pk=fields['points_structure'] )
				event_points.append( (e, ps) )
			
			series.remove_competition( competition )

			for e, ps in event_points:
				sce = SeriesCompetitionEvent( series=series, points_structure=ps )
				sce.event = e
				sce.save()
			
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form_set = get_form_set()
	
	return render( request, 'series_competition_events_form.html', locals() )


#-----------------------------------------------------------------------	
@autostrip
class SeriesPointsStructureForm( ModelForm ):
	class Meta:
		model = SeriesPointsStructure
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(SeriesPointsStructureForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('name', size=20),
			),
			Row(
				Field('points_for_place', size=60),
			),
			Row(
				Field('finish_points'),
				Field('dnf_points'),
				Field('dns_points'),
			),
			Field('category_format', type='hidden'),
			Field('sequence', type='hidden'),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesPointsStructureNew( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	SeriesPointsStructure( series=series, name=datetime.datetime.now().strftime('Points Structure %H:%M:%S') ).save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesPointsStructureEdit( request, seriesPointsStructureId ):
	return GenericEdit( SeriesPointsStructure, request, seriesPointsStructureId, SeriesPointsStructureForm )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesPointsStructureDelete( request, seriesPointsStructureId, confirmed=0 ):
	series_points_structure = get_object_or_404( SeriesPointsStructure, pk=seriesPointsStructureId )
	if int(confirmed):
		series_points_structure.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Delete: '), series_points_structure.name )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesPointsStructureMove( request, moveDirection, seriesPointsStuctureId ):
	series_points_structure = get_object_or_404( SeriesPointsStucture, pk=seriesPointsStuctureId )
	series_points_structure.move( moveDirection )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionMove( request, moveDirection, seriesUpgradeProgressionId ):
	series_upgrade_progression = get_object_or_404( SeriesUpgradeProgression, pk=seriesUpgradeProgressionId )
	series_upgrade_progression.move( moveDirection )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------
class CategorySelectForm( Form ):
	categories = forms.MultipleChoiceField( label=_("Categories in the Series"), help_text=_('Ctrl-Click to Multi-select') )
	
	def __init__( self, *args, **kwargs ):
		series = kwargs.pop( 'series' )
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(CategorySelectForm, self).__init__(*args, **kwargs)
		
		self.fields['categories'].choices = [
			(c.id, string_concat(c.get_gender_display(), u': ', c.code, u' (', c.description, u')'))
				for c in series.category_format.category_set.all()
		]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('categories', size=30),
			)
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoriesChange( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = CategorySelectForm( request.POST, button_mask=EDIT_BUTTONS, series=series )
		if form.is_valid():
			categories = form.cleaned_data['categories']
			
			series.seriesincludecategory_set.all().delete()
			for pk in categories:
				series.seriesincludecategory_set.create( category=Category.objects.get(pk=pk) )
			
			series.normalize()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = CategorySelectForm(
			button_mask=EDIT_BUTTONS,
			series=series,
			initial={'categories':[ic.category.id for ic in series.seriesincludecategory_set.all()]}
		)
	
	return render( request, 'generic_form.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionNew( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	SeriesUpgradeProgression( series=series ).save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionDelete( request, seriesUpgradeProgressionId, confirmed=0 ):
	series_upgrade_progression = get_object_or_404( SeriesUpgradeProgression, pk=seriesUpgradeProgressionId )
	if int(confirmed):
		series_upgrade_progression.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Delete: '), series_upgrade_progression.get_text() )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

class SeriesUpgradeProgressionForm( Form ):
	factor = forms.FloatField( label=_('Points Carry-Forward Factor') )

def GetCategoryProgressionForm( series ):
	class CategoryProgressionForm( Form ):
		category = forms.ChoiceField( label=_('') )
		
		def __init__( self, *args, **kwargs ):
			super(CategoryProgressionForm, self).__init__(*args, **kwargs)		
			self.fields['category'].choices = [(-1, '---')] + [
				(c.pk, string_concat(c.get_gender_display(), u': ', c.code, u' - ', c.description)) for c in series.category_format.category_set.all()]

	return CategoryProgressionForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionEdit( request, seriesUpgradeProgressionId ):
	series_upgrade_progression = get_object_or_404( SeriesUpgradeProgression, pk=seriesUpgradeProgressionId )
	series = series_upgrade_progression.series
	CategoryProgressionFormSet = formset_factory(GetCategoryProgressionForm(series), extra=6)

	ucs = series_upgrade_progression.seriesupgradecategory_set
	
	def get_form():
		return SeriesUpgradeProgressionForm( initial={'factor':series_upgrade_progression.factor}, prefix='progression' )
	
	def get_form_set():
		initial = []
		for uc in ucs.all():
			initial.append( {'category': uc.category.id} )
		return CategoryProgressionFormSet( initial=initial, prefix='categories' )
			
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = SeriesUpgradeProgressionForm( request.POST, prefix='progression' )
		form_set = CategoryProgressionFormSet( request.POST, prefix='categories' )
		if form.is_valid() and form_set.is_valid():
			series_upgrade_progression.factor = abs( form.cleaned_data['factor'] )
			
			seen = set([-1])
			categories = []
			for f in form_set:
				fields = f.cleaned_data
				category = int(fields['category'])
				if category not in seen:
					categories.append( category )
					seen.add( category )

			categories_cur = ucs.all().values_list('pk', flat=True)
			if categories != categories_cur:
				ucs.all().delete()
				
				categories_lookup = Category.objects.in_bulk( categories )
				for seq, pk in enumerate(categories):
					SeriesUpgradeCategory( sequence=seq, category=categories_lookup[pk], upgrade_progression=series_upgrade_progression ).save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			form = get_form()
			form_set = get_form_set()
	else:
		form = get_form()
		form_set = get_form_set()
	
	return render( request, 'series_upgrade_progression_form.html', locals() )
	
#-----------------------------------------------------------------------

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoryGroupNew( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	CategoryGroup( series=series, name=datetime.datetime.now().strftime('Category Group %H:%M:%S') ).save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoryGroupMove( request, moveDirection, categoryGroupId ):
	category_group = get_object_or_404( CategoryGroup, pk=categoryGroupId )
	category_group.move( moveDirection )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoryGroupDelete( request, categoryGroupId, confirmed=0 ):
	category_group = get_object_or_404( CategoryGroup, pk=categoryGroupId )
	if int(confirmed):
		category_group.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Delete: '), category_group.name, u', ', category_group.get_text() )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
class CategoryGroupForm( Form ):
	name = forms.CharField( label=_('Name') )
	categories = forms.MultipleChoiceField( label=_("Categories in the Group"), help_text=_('Ctrl-Click to Multi-select') )
	
	def __init__( self, *args, **kwargs ):
		category_group = kwargs.pop( 'category_group' )
		series = category_group.series
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(CategoryGroupForm, self).__init__(*args, **kwargs)
		

		self.fields['categories'].choices = [(c.id, string_concat(c.get_gender_display(), u': ', c.code, c.description)) for c in series.get_categories_not_in_groups()]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('name', size=30),
			),
			Row(
				Field('categories', size=30),
			),
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoryGroupEdit( request, categoryGroupId ):
	category_group = get_object_or_404( CategoryGroup, pk=categoryGroupId )
	series = category_group.series
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = CategoryGroupForm( request.POST, button_mask=EDIT_BUTTONS, category_group=category_group )
		if form.is_valid():
			categories = form.cleaned_data['categories']
			
			category_group.categorygroupelement_set.all().delete()
			for pk in categories:
				category_group.categorygroupelement_set.create( category=Category.objects.get(pk=pk) )
			
			series.normalize()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = CategoryGroupForm(
			button_mask=EDIT_BUTTONS,
			category_group=category_group,
			initial={'name':category_group.name, 'categories':[ge.category.id for ge in category_group.categorygroupelement_set.all()]}
		)
	
	return render( request, 'generic_form.html', locals() )

