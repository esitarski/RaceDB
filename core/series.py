import operator
from collections import defaultdict

from django.utils.translation import ugettext_lazy as _
from django.forms import formset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

from .views_common import *

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
def SeriesList( request ):
	validate_sequence( Series.objects.all() )		
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

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCopy( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	series.make_copy()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

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
				HTML(_('To hide this Series from all users except Super, start the name with an underscore (_)') )
			),
			Row(
				Field('description', size=40),
			),
			Row(
				Field('ranking_criteria'),
				Field('best_results_to_consider'),
				Field('must_have_completed'),
				HTML('&nbsp;'*4),
				Field('consider_primes'),
			),
			Row( HTML('<hr/>') ),
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
			Row( HTML('<hr/>') ),
			Row(
				Field('callup_max'), HTML( _('Specifies the maximum number of Start Wave Callups.  If zero, this Series will not be used for Callups.') ),
			),
			Row(
				Field('randomize_if_no_results'),
			),
			Row(
				HTML( _('If False, athletes without Series results will not be included in Callups.') ), HTML('<br/>'),
				HTML( _('If True, athletes without Series results will be assigned a random callup.') ),
			),
			Row( HTML('<hr/>') ),
			Row(
				Field('show_last_to_first'),
			),
			Field('category_format', type='hidden'),
			Field('sequence', type='hidden'),
			Field('custom_category_names', type='hidden'),
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
	competitions = [(c, ces) for c, ces in six.iteritems(competitions)]
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
	message = format_lazy( u'{}: {}, {}', _('Delete'), series.name, series.description )
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
		
		categories = set( series.get_categories() )
		events = [e for e in competition.get_events() if not set(e.get_categories()).isdisjoint(categories)]
		events.sort( key=operator.attrgetter('date_time') )
		self.fields['events'].choices = [('{}-{}'.format(e.event_type,e.id), u'{}: {}'.format(e.date_time.strftime('%Y-%m-%d %H:%M'), e.name)) for e in events]
		
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
		categories = set( series.get_categories() )
		for e in competition.get_events():
			if not set(e.get_categories()).isdisjoint(categories):
				sce = SeriesCompetitionEvent( series=series, points_structure=default_points_structure )
				sce.event = e
				sce.save()
				
	existing_competitions = set( series.get_competitions() )
	competitions = Competition.objects.filter( category_format=series.category_format ).order_by('-start_date')
	competitions, paginator = getPaginator( request, page_key, competitions )
	return render( request, 'series_competitions_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCompetitionRemove( request, seriesId, competitionId, confirmed=0 ):
	series = get_object_or_404( Series, pk=seriesId )
	competition = get_object_or_404( Competition, pk=competitionId )
	if int(confirmed):
		series.remove_competition( competition )
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( u'{}: {}:{}', _('Remove'), competition.date_range_year_str, competition.name )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCompetitionRemoveAll( request, seriesId, confirmed=0 ):
	series = get_object_or_404( Series, pk=seriesId )
	if int(confirmed):
		series.seriescompetitionevent_set.all().delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( u'{}: {}', _('Remove All Events from this Series'), series.name )
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
		categories = set( series.get_categories() )
		events = [e for e in competition.get_events() if not set(e.get_categories()).isdisjoint(categories)]
		events.sort( key=operator.attrgetter('date_time') )

		events_included = set( series.get_events_for_competition(competition) )
		points_structure = {ce.event:ce.points_structure.pk for ce in series.seriescompetitionevent_set.all() if ce.event.competition == competition}
		
		initial = [{
			'select': e in events_included,
			'name': timezone.localtime(e.date_time).strftime('%a %H:%M') + ': ' + e.name,
			'points_structure': points_structure.get(e, default_ps),
			'et': e.event_type,
			'pk': e.pk,
		} for e in events]
		
		return EventFormSet( initial=initial )

	if request.method == 'POST':
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
			Field('series', type='hidden'),
			Field('sequence', type='hidden'),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesPointsStructureNew( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	return GenericNew( SeriesPointsStructure, request, SeriesPointsStructureForm, instance_fields={'series':series, 'name':timezone.now().strftime('Series Points %Y-%m-%f %H:%M:S')} )

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
	message = format_lazy( u'{}: {}', _('Delete'), series_points_structure.name )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )
	
#-----------------------------------------------------------------------
class CategorySelectForm( Form ):
	categories = forms.MultipleChoiceField( label=_("Categories in the Series"), widget=forms.CheckboxSelectMultiple )
	custom_categories = forms.MultipleChoiceField( label=_("Custom Categories in the Series"), widget=forms.CheckboxSelectMultiple )
	
	def __init__( self, *args, **kwargs ):
		series = kwargs.pop( 'series' )
		custom_category_names = series.get_all_custom_category_names()
		
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(CategorySelectForm, self).__init__(*args, **kwargs)
		
		self.fields['categories'].choices = [
			(c.id, format_lazy( u'{}: {} ({})', c.get_gender_display(), c.code, c.description))
				for c in series.category_format.category_set.all()
		]
		self.fields['custom_categories'].choices = [(i, cc.name) for i, cc in enumerate(custom_category_names)]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = ''
		
		self.helper.layout = Layout(
			Row( Field('categories', size=30), ),
			Row( Field('custom_categories', size=30), ),
		)
		addFormButtons( self, button_mask )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoriesChange( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	if request.method == 'POST':
		form = CategorySelectForm( request.POST, button_mask=EDIT_BUTTONS, series=series )
		if form.is_valid():
			categories = form.cleaned_data['categories']
			
			series.seriesincludecategory_set.all().delete()
			for pk in categories:
				series.seriesincludecategory_set.create( category=Category.objects.get(pk=pk) )
			
			# Set the custom categories string.
			cc_names = []
			custom_category_names = series.get_all_custom_category_names()
			for v in form.cleaned_data['custom_categories']:
				try:
					cc_names.append( custom_category_names[int(v)] )
				except:
					pass
			series.custom_category_names = ',\n'.join( cc_names )
			series.save()
			
			series.validate()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		custom_category_names = series.get_all_custom_category_names()
		name_id = {cc:i for i, cc in enumerate(custom_category_names)}
		custom_category_i = []
		for name in series.custom_category_names.split(',\n'):
			try:
				custom_category_i.append( name_id[name] )
			except IndexError:
				pass
		form = CategorySelectForm(
			button_mask=EDIT_BUTTONS,
			series=series,
			initial={'categories':[ic.category.id for ic in series.seriesincludecategory_set.all()], 'custom_category_names':custom_category_i, }
		)
	
	return render( request, 'generic_form.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionNew( request, seriesId ):
	series = get_object_or_404( Series, pk=seriesId )
	up = SeriesUpgradeProgression( series=series )
	up.save()
	return HttpResponseRedirect( popPushUrl(request, 'SeriesUpgradeProgressionEdit', up.id) )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesUpgradeProgressionDelete( request, seriesUpgradeProgressionId, confirmed=0 ):
	series_upgrade_progression = get_object_or_404( SeriesUpgradeProgression, pk=seriesUpgradeProgressionId )
	if int(confirmed):
		series_upgrade_progression.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( u'{}: {}', _('Delete'), series_upgrade_progression.get_text() )
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
				(c.pk, format_lazy(u'{}: {} - {}', c.get_gender_display(), c.code, c.description)) for c in series.category_format.category_set.all()
			]

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
	cg = CategoryGroup( series=series, name=datetime.datetime.now().strftime('Category Group %H:%M:%S') )
	cg.save()
	return HttpResponseRedirect( popPushUrl(request, 'SeriesCategoryGroupEdit', cg.id) )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SeriesCategoryGroupDelete( request, categoryGroupId, confirmed=0 ):
	category_group = get_object_or_404( CategoryGroup, pk=categoryGroupId )
	if int(confirmed):
		category_group.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( u'{}: {}, {}', _('Delete'), category_group.name, category_group.get_text() )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
class CategoryGroupForm( Form ):
	name = forms.CharField( label=_('Name') )
	categories = forms.MultipleChoiceField( label=_("Categories in the Group"), widget=forms.CheckboxSelectMultiple )
	
	def __init__( self, *args, **kwargs ):
		category_group = kwargs.pop( 'category_group' )
		series = category_group.series
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(CategoryGroupForm, self).__init__(*args, **kwargs)
		

		self.fields['categories'].choices = [(c.id, format_lazy(u'{}: {} {}', c.get_gender_display(), c.code, c.description)) for c in series.get_categories_not_in_groups()]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = ''
		
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

