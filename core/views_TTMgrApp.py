import datetime
import re
import os
import locale
locale.setlocale(locale.LC_ALL, '')
import datetime
import tempfile
from models import *
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.forms import ModelForm, Form
from django import forms
from django.utils.safestring import mark_safe
import utils
from FitSheetWrapper import FitSheetWrapper
import xlwt
from Excel import GetExcelReader, toAscii
from assignStartTimesLogic import assignStartTimesLogic
from reconcileObservations import reconcileObservations
from results import getUnofficialRank, getResults, getAllPersonalBests, getAllCourseRecords
from DurationField import DurationFormField
from results import getSeriesReportPoints, getSeriesReportAverageSpeed, getLatestCourseRecords

#--------------------------------------------------------------------------------------------
"""
class SpanWidget(forms.Widget):
	'''Renders a value wrapped in a <span> tag.'''

	def render(self, name, value, attrs=None):
		final_attrs = self.build_attrs(attrs, name=name)
		return mark_safe(u'<span%s >%s</span>' % (
			# forms.util.flatatt(final_attrs), self.original_value))
			forms.util.flatatt(final_attrs), self.display_value))

	def value_from_datadict(self, data, files, name):
		return self.original_value
	
def setFormReadOnly( form ):
	for name, field in form.fields.iteritems():
		field.widget = SpanWidget()
		#field.widget.original_value = str(getattr(form.instance, name))
		model_field = form.instance._meta.get_field_by_name(name)[0]
		field.widget.original_value = model_field.value_from_object(form.instance)
		try:
			field.widget.display_value = form.instance['get_%s_display' % name]()
		except:
			field.widget.display_value = field.widget.original_value
	return form
"""
def setFormReadOnly( form ):
	instance = getattr( form, 'instance', None )
	if instance:
		for name, field in form.fields.iteritems():
			field.widget.attrs['readonly'] = True
			field.widget.attrs['disabled'] = True
	return form
	
def getQuery( filter_name, request, queryName = 'q' ):
	if queryName in request.GET:
		query = request.GET[queryName]
	else:
		query = request.session.get(filter_name, '')
	request.session[filter_name] = query
	return query

def applyFilter( query, objects, keyFunc = unicode, doSort = True ):
	if query:
		query = utils.removeDiacritic(query).lower()
		ret = []
		for obj in objects:
			k = utils.removeDiacritic(keyFunc(obj)).lower()
			if k.find(query) >= 0:
				ret.append( obj )
	else:
		ret = list( objects )
	if doSort:
		ret.sort( key = lambda obj: utils.removeDiacritic(keyFunc(obj)).lower() )
	return ret
#--------------------------------------------------------------------------------------------

def index( request ):
	return home( request )

#--------------------------------------------------------------------------------------------

def home( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	return render_to_response( 'home.html', RequestContext(request, locals()) )
	
def tutorial( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	return render_to_response( 'tutorial.html', RequestContext(request, locals()) )
	
#--------------------------------------------------------------------------------------------

class SeriesForm( ModelForm ):
	class Meta:
		model = Series

def displaySeries( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	query = getQuery('series_filter', request)
	series = applyFilter( query, Series.objects.all(), Series.full_name )
	return render_to_response( 'series.html', RequestContext(request, locals()) )

def addSeries( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	title = 'Add Series:'
	
	missing = []
	if not RankingFormat.objects.count(): missing.append( ('No Ranking Formats defined.', path + 'RankingFormats/' ) )
	if missing:
		return render_to_response( 'missing_elements.html', RequestContext(request, locals()) )
	
	if request.method == 'POST':
		form = SeriesForm( request.POST )
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		series = Series()
		# Initalize the ranking format to the first one.
		for ranking_format in RankingFormat.objects.all():
			series.ranking_format = ranking_format
			break
		form = SeriesForm( instance = series )
	return render_to_response( 'add_edit_series.html', RequestContext(request, locals()) )
	
def editSeries( request, seriesId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	series = get_object_or_404( Series, pk=seriesId )
	title = 'Edit Series:'
	if request.method == 'POST':
		form = SeriesForm( request.POST )
		if form.is_valid():
			seriesForm = form.save( commit = False )
			seriesForm.id = series.id
			seriesForm.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = SeriesForm( instance = series )
	return render_to_response( 'add_edit_series.html', RequestContext(request, locals()) )
	
def copySeries( request, seriesId ):
	path = request.path
	cancelUrl = utils.cancelUrl( path )
	series = get_object_or_404( Series, pk=seriesId )
	series.id = None
	series.name = '%s - Copy' % series.name
	series.save()
	return HttpResponseRedirect(cancelUrl)
	
def removeSeries( request, seriesId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	series = get_object_or_404( Series, pk=seriesId )
	title = 'Remove Series:'
	if request.method == 'POST':
		series.delete()
		return HttpResponseRedirect(cancelUrl)
	else:
		form = setFormReadOnly( SeriesForm(instance = series) )
	return render_to_response( 'add_edit_series.html', RequestContext(request, locals()) )
	
def reportSeries( request, seriesId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	series = get_object_or_404( Series, pk=seriesId )
	events = list( Event.objects.filter(series = series) )
	if series.ranking_policy == 'P':
		results = getSeriesReportPoints( series )
		return render_to_response( 'series_report_points.html', RequestContext(request, locals()) )
	else:
		results = getSeriesReportAverageSpeed( series )
		return render_to_response( 'series_report_average_speed.html', RequestContext(request, locals()) )

def helpSeries( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	return render_to_response( 'help_series.html', RequestContext(request, locals()) )

#--------------------------------------------------------------------------------------------

class RankingFormatForm( ModelForm ):
	class Meta:
		model = RankingFormat

def displayRankingFormats( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	query = getQuery('ranking_format_filter', request)
	ranking_formats = applyFilter( query, RankingFormat.objects.all(), RankingFormat.full_name )
	return render_to_response( 'ranking_format.html', RequestContext(request, locals()) )

def addRankingFormat( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	title = 'Add Ranking Format:'
	if request.method == 'POST':
		form = RankingFormatForm( request.POST )
		if form.is_valid():
			rf = form.save()
			return HttpResponseRedirect('%s/Edit/%d/' % (breadcrumbs[-2].url, rf.id))
	else:
		form = RankingFormatForm()
	return render_to_response( 'add_ranking_format.html', RequestContext(request, locals()) )
		
def editRankingFormat( request, rankingFormatId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	categories = Category.objects.filter( format = ranking_format )
	readWrite = True
	title = 'Edit Ranking Format:'
	if request.method == 'POST':
		form = RankingFormatForm( request.POST )
		if form.is_valid():
			rankingFormatForm = form.save( commit = False )
			rankingFormatForm.id = ranking_format.id
			rankingFormatForm.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = RankingFormatForm( instance = ranking_format )
	return render_to_response( 'edit_ranking_format.html', RequestContext(request, locals()) )
	
def removeRankingFormat( request, rankingFormatId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	categories = Category.objects.filter( format = ranking_format )
	readWrite = False
	if not Series.objects.filter(ranking_format = ranking_format).count():
		title = 'Remove Ranking Format (and all its Categories):'
	else:
		title = 'Warning: Ranking Format in use!  Removing it will lose results.  Are you sure?'

	if request.method == 'POST':
		ranking_format.delete()
		return HttpResponseRedirect(cancelUrl)
	else:
		form = setFormReadOnly( RankingFormatForm(instance = ranking_format) )
	return render_to_response( 'edit_ranking_format.html', RequestContext(request, locals()) )
	
def copyRankingFormat( request, rankingFormatId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	categories = Category.objects.filter( format = ranking_format )
	ranking_format.id = None
	ranking_format.name = '%s - Copy' % ranking_format.name
	ranking_format.save()
	for cat in categories:
		cat.id = None
		cat.format = ranking_format
		cat.save()
	return HttpResponseRedirect(cancelUrl)
	
#--------------------------------------------------------------------------------------------
class CategoryForm( ModelForm ):
	class Meta:
		model = Category
		fields = ('code', 'gender', 'description')

def displayCategories( request, rankingFormatId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	query = getQuery('category_filter', request)
	ranking_formats = applyFilter( query, RankingFormat.objects.all(), RankingFormat.full_name )
	return render_to_response( 'ranking_format.html', RequestContext(request, locals()) )

def addCategory( request, rankingFormatId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	title = 'Add Category:'
	if request.method == 'POST':
		form = CategoryForm( request.POST )
		if form.is_valid():
			categoryForm = form.save( commit = False )
			categoryForm.format = ranking_format
			categoryForm.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = CategoryForm()
	return render_to_response( 'add_edit_category.html', RequestContext(request, locals()) )
	
def editCategory( request, rankingFormatId, categoryId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	category = get_object_or_404( Category, pk=categoryId )
	title = 'Edit Category:'
	if request.method == 'POST':
		form = CategoryForm( request.POST )
		if form.is_valid():
			categoryForm = form.save( commit = False )
			for f in CategoryForm.Meta.fields:
				setattr(category, f, getattr(categoryForm, f))
			category.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = CategoryForm( instance = category )
	return render_to_response( 'add_edit_category.html', RequestContext(request, locals()) )
	
def removeCategory( request, rankingFormatId, categoryId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	ranking_format = get_object_or_404( RankingFormat, pk=rankingFormatId )
	category = get_object_or_404( Category, pk=categoryId )
	readWrite = False
	if not Entry.objects.filter(category = category).count():
		title = 'Remove Category:'
	else:
		title = 'Warning: Category in use!  Removing it will lose results.  Are you sure?'
	if request.method == 'POST':
		category.delete()
		return HttpResponseRedirect(cancelUrl)
	else:
		form = setFormReadOnly( CategoryForm(instance = category) )
	return render_to_response( 'add_edit_category.html', RequestContext(request, locals()) )

#--------------------------------------------------------------------------------------------

class CourseForm( ModelForm ):
	class Meta:
		model = Course

def displayCourses( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	query = getQuery('course_filter', request)
	courses = applyFilter( query, Course.objects.all(), Course.full_name )
	latestCourseRecords = getLatestCourseRecords()
	for c in courses:
		entry = latestCourseRecords.get(c, None)
		if not entry:
			c.record_holder_name = ''
			c.record_holder_time = ''
			c.record_holder_date = ''
		else:
			c.record_holder_name = entry.rider.full_name()
			c.record_holder_time = utils.formatTimeHHMMSS( entry.final_time.total_seconds() )
			c.record_holder_date = entry.event.date.strftime( '%Y-%m-%d' )
			
	return render_to_response( 'courses.html', RequestContext(request, locals()) )

def addCourse( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	title = 'Add Course:'
	if request.method == 'POST':
		form = CourseForm( request.POST )
		if form.is_valid():
			form.save()
			request.session['course_filter'] = ''
			return HttpResponseRedirect(cancelUrl)
	else:
		form = CourseForm()
	return render_to_response( 'add_edit_course.html', RequestContext(request, locals()) )
		
def editCourse( request, courseId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	course = get_object_or_404( Course, pk=courseId )
	title = 'Edit Course:'
	if request.method == 'POST':
		form = CourseForm( request.POST )
		if form.is_valid():
			courseForm = form.save( commit = False )
			courseForm.id = course.id
			courseForm.save()
			request.session['course_filter'] = ''
			return HttpResponseRedirect(cancelUrl)
	else:
		form = CourseForm( instance = course )
	return render_to_response( 'add_edit_course.html', RequestContext(request, locals()) )
	
def removeCourse( request, courseId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	course = get_object_or_404( Course, pk=courseId )
	title = 'Remove Course:'
	if request.method == 'POST':
		course.delete()
		return HttpResponseRedirect(cancelUrl)
	else:
		form = setFormReadOnly( CourseForm(instance = course) )
	return render_to_response( 'add_edit_course.html', RequestContext(request, locals()) )
	
#--------------------------------------------------------------------------------------------

def events( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	events = Event.objects.all()
	return render_to_response( 'events.html', RequestContext(request, locals()) )

class EventForm( ModelForm ):
	class Meta:
		model = Event
		fields = ('name', 'series', 'courses', 'date', 'points_multiplier', 'start_time', 'registration_status', 'wind_from', 'wind_strength')
	
def editEvent( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = '../../'
	event = get_object_or_404( Event, pk=eventId )
	title = 'Edit Event' if event else 'Add Event'
	if request.method == 'POST':
		form = EventForm( request.POST, instance = event )
		if form.is_valid():
			eventForm = form.save( commit = False )
			formFields = set(EventForm.Meta.fields)
			for f in Event._meta.fields:
				if f.name not in formFields:
					setattr( eventForm, f.name, getattr(event, f.name) )
			eventForm.save()
			form.save_m2m()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = EventForm( instance = event )
	return render_to_response( 'add_edit_event.html', RequestContext(request, locals()) )
	
def addEvent( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = '../'
	
	missing = []
	if not Series.objects.count():	missing.append( ('No Series defined.', path + 'Series/') )
	if not Course.objects.count():	missing.append( ('No Courses defined.', path + 'Courses/') )
	if missing:
		return render_to_response( 'missing_elements.html', RequestContext(request, locals()) )
	
	title = 'Add Event'
	if request.method == 'POST':
		form = EventForm( request.POST )
		if form.is_valid():
			form.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		event = Event()
		event.date = datetime.date.today()
		event.start_time = datetime.time( 9, 0, 0 )
		form = EventForm( instance = event )
	return render_to_response( 'add_edit_event.html', RequestContext(request, locals()) )
	
def removeEvent( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	if request.method == 'POST':
		event.delete()
		return HttpResponseRedirect( cancelUrl )
	form = setFormReadOnly( EventForm(instance = event) )
	return render_to_response( 'add_edit_event.html', RequestContext(request, locals()) )

def selectEvent( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	title = unicode(event)
	return render_to_response( 'tasks.html', RequestContext(request, locals()) )
	
class SeriesModelForm( ModelForm ):
	class Meta:
		model = Series
		
def addEditSeries( request, seriesId=None ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	series = get_object_or_404( Series, pk=riderId ) if seriesId is not None else None
	title = 'Edit Series' if series else 'New Series'
	if request.method == 'POST':
		form = SeriesModelForm( request.POST )
		if form.is_valid():
			form.save()
			return HttpResponseRedirect( cancelUrl )
	else:
		form = SeriesModelForm( instance = series ) if series else SeriesModelForm() 
	return render_to_response( 'add_edit_series.html', RequestContext(request, locals()) )
	
def registration( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = breadcrumbs[-2].url
	event = get_object_or_404( Event, pk=eventId )
	
	if 'q' in request.GET:
		query = request.GET['q']
	else:
		query = request.session.get('registration_rider_filter', '')
	request.session['registration_rider_filter'] = query
		
	entries = list( Entry.objects.select_related('rider').filter(event=event) )
	if query:
		query = utils.removeDiacritic(query).lower()
		entries = [e for e in entries if (utils.removeDiacritic(e.rider.full_name())+','+str(e.bib)).lower().find(query) >= 0]
	entries.sort( key = lambda e: utils.removeDiacritic(e.rider.full_name()).lower() )
	resultsCount = len(entries)
	return render_to_response( 'registration.html', RequestContext(request, locals()) )

def findRider( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	
	enteredRiderIds = set( e.rider.id for e in Entry.objects.select_related('rider').filter(event = event) )
	
	if 'q' in request.GET:
		query = request.GET['q']
	else:
		query = request.session.get('find_rider_filter', '')
	request.session['find_rider_filter'] = query
	
	riders = []
	if query:
		query = utils.removeDiacritic(query).lower()
		for rider in Rider.objects.all():
			name = utils.removeDiacritic(rider.full_name()).lower()
			if name.find(query) >= 0:
				riders.append( rider )
	else:
		riders = list(Rider.objects.all())
	riders.sort( key = lambda rider: utils.removeDiacritic(rider.full_name()).lower() )
	if len(riders) > 200:
		riders = riders[:200]

	for r in riders:
		setattr( r, 'entered', r.id in enteredRiderIds )
	
	return render_to_response( 'find_rider.html', RequestContext(request, locals()) )

#---------------------------------------------------------------------------------------------------

class EntryForm( ModelForm ):
	def __init__( self, event, rider, *args, **kwargs ):
		super(EntryForm, self).__init__(*args, **kwargs)
		self.fields['bib'].required = True
		self.fields['category'].queryset = Category.objects.filter(	Q(format = event.series.ranking_format),
																	Q(gender = 'O') | Q(gender = rider.gender) )
		courseIds = [course.id for course in event.courses.all()]
		self.fields['course'].queryset = Course.objects.filter(pk__in = courseIds)
		self.fields['est_speed'].required = True
		self.fields['start_time'].required = False
	class Meta:
		model = Entry
		fields = ('bib','category','course','start_wave','est_speed','start_rank','start_time','status')

def validateEntry( event, rider, entry ):
	errorMsg = ''
	if not errorMsg:
		bibConflict = Entry.objects.filter( Q(event = event) & Q(start_wave = entry.start_wave) & Q(bib = entry.bib) & ~Q(pk = entry.pk) )
		for c in bibConflict:
			errorMsg = '%s is already riding with Bib %d in wave %s.  Please choose another Bib.' % (
						 c.rider.full_name(), c.bib, c.start_wave )
			break
	if not errorMsg:
		riderConflict = Entry.objects.filter( Q(event = event) & Q(start_wave = entry.start_wave) & Q(rider = rider) & ~Q(pk = entry.pk) )
		for c in riderConflict:
			errorMsg = '%s has already been added to this wave as Bib %d.' % (
						c.rider.full_name(), c.bib )
			break
	return errorMsg

def initEntry( entry, event, rider ):
	# Try to find some intitial values for this rider.
	
	# Assign a default course.
	courses = list( event.courses.all() )
	entry.course = courses[0]	# Default to the first course.
	courseIds = set(course.id for course in courses)
	
	# Get all the events this rider participated in.
	entries = list(Entry.objects.select_related('rider', 'course', 'category').filter(rider = rider))
	if not entries:
		return
	entries.sort( key = lambda e: e.event.date, reverse=True )
	
	inMiles = (entry.course.distance_unit == 'M')
	
	# Try to find the rider's category from a previous event.
	for e in entries:
		if event.series.ranking_format == e.category.format:
			entry.category = e.category
			break
	
	# Try to find the rider's course in a previous event.
	for e in entries:
		if e.course.id in courseIds:
			entry.est_speed = e.ride_speed(inMiles)
			entry.course = e.course
			return
		
	# Get the terrain of one of the event courses.
	for course in event.courses.all():
		terrain = course.terrain
		break
	
	# Try to find an event with the same terrain.
	for e in entries:
		if e.course.terrain == terrain:
			entry.est_speed = e.ride_speed(inMiles)
			return

def addEntry( request, eventId, riderId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	
	event = get_object_or_404( Event, pk=eventId )
	rider = get_object_or_404( Rider, pk=riderId )
	rider_age = datetime.date.today().year - rider.date_of_birth.year
	
	entries = Entry.objects.filter( event=event, rider=rider )
	if entries:
		error = u'%s has been entered already.' % rider.full_name()
		return render_to_response( 'error.html', RequestContext(request, locals()) )
	
	title = u'Add Rider: %s' % rider.full_name()
	errorMsg = ''
	if request.method == 'POST':
		entries = Entry.objects.filter( event=event, rider=rider )
		if entries:
			error = u'%s has been entered already.' % rider.full_name()
			return render_to_response( 'error.html', RequestContext(request, locals()) )
			
		form = EntryForm( event, rider, request.POST )
		if form.is_valid():
			entry = form.save( commit = False )
			errorMsg = validateEntry( event, rider, entry )
			if not errorMsg:
				entry.event = event
				entry.rider = rider
				entry.save()
				return HttpResponseRedirect(breadcrumbs[-3].url)
	else:
		entry = Entry()
		initEntry( entry, event, rider )
		form = EntryForm( event, rider, instance = entry )
	return render_to_response( 'add_edit_entry.html', RequestContext(request, locals()) )
	
def editEntry( request, eventId, entryId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = breadcrumbs[-2].url
	event = get_object_or_404( Event, pk=eventId )
	entry = get_object_or_404( Entry, pk=entryId )
	rider = entry.rider
	rider_age = datetime.date.today().year - rider.date_of_birth.year
	entries = Entry.objects.filter( rider = rider ).order_by( '-event__date' )
	
	title = 'Edit Entry: %s' % rider.full_name()
	errorMsg = ''
	if request.method == 'POST':
		form = EntryForm( event, rider, request.POST )
		if form.is_valid():
			entryForm = form.save( commit = False )
			for f in EntryForm.Meta.fields:
				setattr(entry, f, getattr(entryForm, f))
			errorMsg = validateEntry( event, rider, entry )
			if not errorMsg:
				entry.save()
				return HttpResponseRedirect(cancelUrl)
	else:
		form = EntryForm( event, rider, instance = entry )
	return render_to_response( 'add_edit_entry.html', RequestContext(request, locals()) )

#---------------------------------------------------------------------------------------------------

def removeEntry( request, eventId, entryId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = breadcrumbs[-2].url
	event = get_object_or_404( Event, pk=eventId )
	entry = get_object_or_404( Entry, pk=entryId )
	rider = entry.rider
	form = setFormReadOnly( EntryForm(event, rider, instance = entry) )
	if request.method == 'POST':
		entry.delete()
		return HttpResponseRedirect( cancelUrl )
	return render_to_response( 'remove_entry.html', RequestContext(request, locals()) )

#---------------------------------------------------------------------------------------------------

class RiderModelForm( ModelForm ):
	class Meta:
		model = Rider
		fields = (
			'first_name',
			'last_name',
			'gender',
			'date_of_birth',
			'team',
			'license',
			'email',
		)
		
def displayRiders( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	query = getQuery('rider_filter', request)
	riders = applyFilter( query, Rider.objects.all(), Rider.full_name )
	return render_to_response( 'riders.html', RequestContext(request, locals()) )
	
def addRider( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	entries = []
	title = 'Add:'
	if request.method == 'POST':
		form = RiderModelForm( request.POST )
		if form.is_valid():
			form.save()
			return HttpResponseRedirect( cancelUrl )
	else:
		form = RiderModelForm()
	return render_to_response( 'add_edit_rider.html', RequestContext(request, locals()) )
	
def editRider( request, riderId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	rider = get_object_or_404( Rider, pk=riderId )
	entries = Entry.objects.filter( rider = rider ).order_by( '-event__date' )
	title = 'Edit:'
	if request.method == 'POST':
		form = RiderModelForm( request.POST )
		if form.is_valid():
			riderForm = form.save( commit = False )
			for f in form.fields:
				setattr(rider, f, getattr(riderForm, f))
			rider.save()
			return HttpResponseRedirect( cancelUrl )
	else:
		form = RiderModelForm( instance = rider )
	return render_to_response( 'add_edit_rider.html', RequestContext(request, locals()) )
	
def removeRider( request, riderId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	rider = get_object_or_404( Rider, pk=riderId )
	entries = Entry.objects.filter( rider = rider ).order_by( '-event__date' )
	title = 'Remove:'
	if request.method == 'POST':
		rider.delete()
		return HttpResponseRedirect( cancelUrl )
	else:
		form = setFormReadOnly( RiderModelForm(instance = rider) )
	return render_to_response( 'add_edit_rider.html', RequestContext(request, locals()) )
	
#---------------------------------------------------------------------------------------------------

class AssignStartTimesForm( ModelForm ):
	class Meta:
		model = Event
		fields = (
			'start_time',
			'first_rider_gap',
			'start_gap',
			'heat_size',
			'wave_gap',
			'num_fastest_riders',
			'fastest_riders_gap',
		)
		
def getStartTimeEntries( event ):
	entries = list( Entry.objects.filter(event = event, status = Entry.STATUS_CHOICES[0][0]) )
	now_time = datetime.datetime.now()
	today = datetime.datetime.combine( datetime.date.today(), datetime.time(0,0,0) )
	event_start_time = datetime.datetime.combine(today, event.start_time)
	entries.sort( key = lambda e: (today + e.start_time if e.start_time else now_time, e.registration_timestamp) )

	# Add the clock start time.
	tStart = []
	for e in entries:
		try:
			t = (event_start_time + e.start_time).time()
		except TypeError:
			t = None
		setattr( e, 'clock_start_time', t )
		setattr( e, 'gap_change_before', False )
		try:
			est_finish_time = (datetime.datetime.combine(today, t) + e.est_ride_time).time()
		except TypeError:
			est_finish_time = None
		setattr( e, 'est_finish_time', est_finish_time )
		if t is not None:
			tStart.append( t.hour * (60*60) + t.minute * 60 + t.second )

	# Add empty rows in the table between changes in waves and start time.
	# Add the breaks for the waves.
	for i in xrange(1, len(entries)):
		if not entries[i].start_time:
			break
		if entries[i-1].start_wave != entries[i].start_wave:
			setattr( entries[i], 'gap_change_before', True )
		
	# Add the breaks for the entries taking the start heats into account.
	tiStart = [(t, i) for i, t in enumerate(tStart)]
	tiStart = utils.uniquify( tiStart, lambda x: x[0] )
	
	tiiDelta = [(tiStart[i][0] - tiStart[i-1][0], tiStart[i-1][1], tiStart[i][1]) for i in xrange(1, len(tiStart))]
	for i in xrange(1, len(tiiDelta)):
		if tiiDelta[i][0] != tiiDelta[i-1][0]:
			setattr( entries[tiiDelta[i][2]], 'gap_change_before', True )
			
	return entries

def assignStartTimes( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	today = datetime.date.today()
	if request.method == 'POST':
		form = AssignStartTimesForm( request.POST )
		if event.registration_status == '1' and form.is_valid():
			ast = dict( [(name, form.cleaned_data[name]) for name, field in form.fields.iteritems()] )
			ast['event'] = event
			
			eventForm = form.save( commit = False )
			for f in form.fields:
				setattr(event, f, getattr(eventForm, f))
		
			assignStartTimesLogic( **ast )
	else:
		if event.registration_status == '1' and not event.start_time:
			t = datetime.now().replace( second = 0, microsecond = 0 )
			t += timedelta( seconds = 4*60 )
			t += timedelta( seconds = (5 - t.minute % 5) * 60 )
			event.start_time = t.time()
		form = AssignStartTimesForm( instance = event )
		
	if event.registration_status != '1':
		form = setFormReadOnly( form )
		errorMsg = 'Registration is closed.  Start times can no longer be assigned.  To reopen registration, go to "Start Race."'
	else:
		errorMsg = ''
		
	event_start_time = datetime.datetime.combine(today, event.start_time)
	entries = getStartTimeEntries( event )
	editable = True
	return render_to_response( 'assign_start_times.html', RequestContext(request, locals()) )
	
def startTimesPrintable( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	entries = getStartTimeEntries( event )
	editable = False
	return render_to_response( 'start_times_printable.html', RequestContext(request, locals()) )

#---------------------------------------------------------------------------------------------------------------------

class StartRaceForm( ModelForm ):
	class Meta:
		model = Event
		fields = (
			'registration_status',
			'stopwatch_start_time',
		)
		
def startRace( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	if request.method == 'POST':
		form = StartRaceForm( request.POST )
		if form.is_valid():
			eventForm = form.save( commit = False )
			for f in form.fields:
				setattr(event, f, getattr(eventForm, f))
			event.save()
			return HttpResponseRedirect( cancelUrl )
	else:
		form = StartRaceForm( instance = event )
	return render_to_response( 'start_race.html', RequestContext(request, locals()) )
	
#--------------------------------------------------------------------------------------------

class RecordFinishForm( Form ):
	time_0 = DurationFormField( required=False )
	bib_0 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_1 = DurationFormField( required=False )
	bib_1 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_2 = DurationFormField( required=False )
	bib_2 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_3 = DurationFormField( required=False )
	bib_3 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_4 = DurationFormField( required=False )
	bib_4 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_5 = DurationFormField( required=False )
	bib_5 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_6 = DurationFormField( required=False )
	bib_6 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )
	time_7 = DurationFormField( required=False )
	bib_7 = forms.IntegerField( required=False, min_value = 0, max_value = 99999 )

def recordFinishTimes( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	if request.method == 'POST':
		form = RecordFinishForm( request.POST )
		if form.is_valid():
			dTime = None
			for i, (name, field) in enumerate(form.fields.iteritems()):
				if (i % 2) == 0:
					dTime = form.cleaned_data[name]
				else:
					if dTime:
						ob = Observation( event = event, time = dTime, bib = form.cleaned_data[name] )
						ob.save()
	
	reconcileObservations( event )
	form = RecordFinishForm()
	
	# Always use today's date!
	event_date = datetime.date.today()
	if event.stopwatch_start_time:
		event_start = datetime.datetime.combine( event_date, datetime.time(0,0,0) ) + event.stopwatch_start_time
	else:
		event_start = datetime.datetime.combine( event_date, event.start_time )
	
	event_start_str = '%d,%d,%d,%d,%d,%d,%d' % (
		event_start.year,
		event_start.month - 1,
		event_start.day,
		event_start.hour,
		event_start.minute,
		event_start.second,
		int(event_start.microsecond / 1000.0) )		# Convert microseconds to milliseconds.
	
	observations = list( Observation.objects.select_related('event').filter( event = event ).order_by('-time') )
	obId = dict( (ob.id, ob) for ob in observations )
	rank = getUnofficialRank( event )
	for e in Entry.objects.filter( event = event ):
		if e.observation is None:
			continue
		ob = obId.get(e.observation.id, None)
		if ob is None:
			continue
		setattr( ob, 'bib', e.bib )
		setattr( ob, 'rider', e.rider )
		setattr( ob, 'start_time', e.start_time )
		setattr( ob, 'finish_time', e.finish_time )
		setattr( ob, 'ride_time', e.ride_time )
		setattr( ob, 'speed', e.ride_speed_text() )
		setattr( ob, 'category', e.category )
		setattr( ob, 'course', e.course )
		setattr( ob, 'rank', rank.get(e.id, '') )
	
	return render_to_response( 'record_finish_times.html', RequestContext(request, locals()) )

class ObservationForm( ModelForm ):
	class Meta:
		model = Observation
		fields = (
			'time',
			'bib',
		)
		
def editObservation( request, eventId, observationId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	observation = get_object_or_404( Observation, pk=observationId )
	if request.method == 'POST':
		form = ObservationForm( request.POST )
		if form.is_valid():
			observationForm = form.save( commit = False )
			for f in form.fields:
				setattr(observation, f, getattr(observationForm, f))
			observation.save()
			reconcileObservations( event )
			return HttpResponseRedirect( cancelUrl )
	else:
		form = ObservationForm( instance = observation )
	return render_to_response( 'edit_observation.html', RequestContext(request, locals()) )
	
def removeObservation( request, eventId, observationId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	observation = get_object_or_404( Observation, pk=observationId )
	if request.method == 'POST':
		observation.delete()
		return HttpResponseRedirect( cancelUrl )
	form = setFormReadOnly( ObservationForm(instance = observation) )
	return render_to_response( 'remove_observation.html', RequestContext(request, locals()) )
	
#--------------------------------------------------------------------------------------------

class EntryFinalizeResults( ModelForm ):
	def __init__( self, event, rider, *args, **kwargs ):
		super(EntryFinalizeResults, self).__init__(*args, **kwargs)
		self.fields['bib'].required = True
		self.fields['start_time'].required = False
		self.fields['finish_time'].required = False
		self.fields['category'].queryset = Category.objects.filter(	Q(format = event.series.ranking_format),
																	Q(gender = 'O') | Q(gender = rider.gender) )
		courseIds = [course.id for course in event.courses.all()]
		self.fields['course'].queryset = Course.objects.filter(pk__in = courseIds)
	class Meta:
		model = Entry
		fields = (
				'bib','category','course','status',
				'start_time', 'finish_time',
				'start_time_early',
	
				'adjustment_name_1', 'adjustment_time_1', 'adjustment_count_1',
				'adjustment_name_2', 'adjustment_time_2', 'adjustment_count_2',
		)

def editResult( request, eventId, entryId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	entry = get_object_or_404( Entry, pk=entryId )
	rider = entry.rider
	
	if request.method == 'POST':
		form = EntryFinalizeResults( event, rider, request.POST )
		if form.is_valid():
			entryForm = form.save( commit = False )
			for f in form.fields:
				setattr(entry, f, getattr(entryForm, f))
			entry.save()
			return HttpResponseRedirect(cancelUrl)
	else:
		form = EntryFinalizeResults( event, rider, instance = entry )
		
	return render_to_response( 'edit_result.html', RequestContext(request, locals()) )
		
def finalizeResults( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	
	if 'q' in request.GET:
		query = request.GET['q']
	else:
		query = request.session.get('finalize_results_filter', '')
	request.session['finalize_results_filter'] = query
	
	entries = list( Entry.objects.select_related('rider').filter(event = event) )
	if query:
		query = utils.removeDiacritic(query).lower()
		entries = [e for e in entries if (utils.removeDiacritic(e.rider.full_name())+','+str(e.bib)).lower().find(query) >= 0]
			
	entries.sort( key = lambda e: utils.removeDiacritic(e.rider.full_name()).lower() )
	
	return render_to_response( 'finalize_results.html', RequestContext(request, locals()) )
	
def showResults( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	readWrite = False
	
	results = getResults( event )
	return render_to_response( 'results.html', RequestContext(request, locals()) )
	
def printResults( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	readWrite = False
	
	results = getResults( event )
	return render_to_response( 'print_results.html', RequestContext(request, locals()) )

reDisallowedFileNameChars = re.compile( r'''['"*/:<>?\\|]''' )
	
def downloadResults( request, eventId ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	event = get_object_or_404( Event, pk=eventId )
	
	filename = toAscii(reDisallowedFileNameChars.sub('', "TTMgrResults_%s_%s.xls" % (event.name, event.date.isoformat())))

	response = HttpResponse(mimetype="application/ms-excel")
	response['Content-Disposition'] = 'attachment; filename=%s' % filename
	
	wb = xlwt.Workbook()
	
	fnt = xlwt.Font()
	fnt.name = 'Arial'
	fnt.bold = True
	fnt.height = int(fnt.height * 1.2)
	
	titleStyle = xlwt.XFStyle()
	titleStyle.font = fnt
	
	fnt = xlwt.Font()
	fnt.name = 'Arial'
	fnt.bold = True
	headerStyle = xlwt.XFStyle()
	headerStyle.font = fnt
	
	reDisallowedChars = re.compile( '''[:/?*\[\]\\']''' )
	for result in getResults(event):
		ws = wb.add_sheet( reDisallowedChars.sub( '-', '%s, %s' % (result['category'], result['course']))[:30] )
		fws = FitSheetWrapper( ws )
		
		rCur = 0
		ws.write_merge( rCur, rCur, 0, 10, 'Event: %s (%s)' % (event.name, event.date.isoformat()), titleStyle )
		rCur += 1
		ws.write_merge( rCur, rCur, 0, 10, 'Series: %s' % event.series.name, titleStyle )
		rCur += 2
		ws.write_merge( rCur, rCur, 0, 10, '%s, %s' % (result['category'], result['course']), titleStyle )
		rCur += 1
		ws.write_merge( rCur, rCur, 0, 10, 'Ave Speed: %s' % result['ave_speed'], titleStyle )
		rCur += 2
		
		for c, f in enumerate(['Place', 'Bib', 'Name', 'Team', 'Time', 'Gap']):
			fws.write( rCur, c, f, headerStyle )
		rCur += 1
		
		for r, entry in enumerate(result['entries']):
			if entry.get_final_status_display == 'Finisher':
				fws.write( rCur, 0, r + 1 )
			else:
				fws.write( rCur, 0, entry.get_final_status_display )
				
			fws.write( rCur, 1, entry.bib )
			fws.write( rCur, 2, entry.rider.full_name() )
			fws.write( rCur, 3, entry.rider.team if entry.rider.team else '' )
			fws.write( rCur, 4, entry.final_time if entry.final_time else '' )
			fws.write( rCur, 5, entry.gap_time if entry.gap_time else '' )
			rCur += 1
			
	wb.save( response )
	return response
	
#---------------------------------------------------------------------------------------------

def handle_uploaded_file( f ):
	fn, ext = os.path.splitext( f.name )
	if ext not in ['.csv', '.xls', '.xlsx', '.xlsm']:
		raise TypeError, 'File must be in .xlsx, .xlsm, .xls or .csv format.'
	fd, fname = tempfile.mkstemp( prefix='TTMgr', suffix=ext )
	destination = os.fdopen( fd, 'w' )
	for chunk in f.chunks():
		destination.write(chunk)
	destination.close()
	
	reader = GetExcelReader( fname )
	sheet_name = reader.sheet_names()[0]
	
	riderMap = {}
	for rider in Rider.objects.all():
		riderMap[(toAscii(rider.first_name).lower(), toAscii(rider.last_name).lower(), rider.gender, rider.date_of_birth)] = rider.id
		
	headerMap = {}
	fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'team', 'license', 'email']
	key_fields = set( fields[:4] )
	for rowCount, row in enumerate(reader.iter_list(sheet_name)):
		if not row or not any( d for d in row ):
			continue
		if not headerMap:
			# Get the header row.
			header = row
			for i, h in enumerate(header):
				for f in fields:
					if f.replace('_', '') == toAscii(h).lower().replace(' ', ''):
						headerMap[f] = i
						break
			missing = []
			for f in fields[:4]:
				if f not in headerMap:
					missing.append( f )
			if missing:
				raise TypeError, 'Missing required header columns:' % (', '.join(missing))
			continue
			
		# Process this row
		rider = Rider()
		for f, c in headerMap.iteritems():
			if not row[c]:
				if f in key_fields:
					raise TypeError, 'Missing required field (row=%d, column=%d)' % (rowCount + 1, c + 1)
				else:
					continue
			d = row[c]
			if f == 'date_of_birth':
				try:
					year, month, day = [int(n) for n in d.split('-')]
					d = datetime.date( year = year, month = month, day = day )
				except:
					raise TypeError, 'Invalid date field (row=%d, column=%d)' % (rowCount + 1, c + 1)
			elif f == 'gender':
				d = 'F' if d and d[0].upper() != 'M' else 'M'
			setattr( rider, f, d )
		
		# Check if this is an insert or an update.
		riderKey = (toAscii(rider.first_name).lower(), toAscii(rider.last_name).lower(), rider.gender, rider.date_of_birth)
		try:
			rider_existing = Rider.objects.get(pk = riderMap[riderKey])
			
			# We found a matching existing rider - update the fields we read from the upload.
			for f, c in headerMap.iteritems():
				if f not in key_fields:
					setattr( rider_existing, f, getattr(rider, f) )
			rider_existing.save()
		except (KeyError, Rider.DoesNotExist):
			rider.save()	# This is a new rider - insert it into the db.
			riderMap[riderKey] = rider.id	# Update our cache.

	if not headerMap:
		raise TypeError, 'No header row found.'
		
class UploadFileForm( Form ):
	file = forms.FileField()

def uploadRiders( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			f = request.FILES['file']
			fname, ext = os.path.splitext( f.name )
			try:
				handle_uploaded_file(request.FILES['file'])
				return HttpResponseRedirect( cancelUrl )
			except TypeError as e:
				errors = [e.message]
				return render_to_response('upload_riders_error.html', RequestContext(request, locals()) )
		else:
			error = ['Validation failed (missing file?).']
			return render_to_response('upload_riders_error.html', RequestContext(request, locals()) )
	else:
		form = UploadFileForm()
	return render_to_response('upload_riders.html', RequestContext(request, locals()) )
	
def downloadRiders( request ):
	path = request.path
	breadcrumbs = utils.breadcrumbsFromPath( path )
	cancelUrl = utils.cancelUrl( path )
	riders = Rider.objects.all()
	
	filename = "TTMgrRiders_%s.xls" % datetime.date.today().isoformat()

	response = HttpResponse(mimetype="application/ms-excel")
	response['Content-Disposition'] = 'attachment; filename=%s' % filename
	
	wb = xlwt.Workbook()
	aws = wb.add_sheet( 'Riders' )
	ws = FitSheetWrapper( aws )
	
	for c, f in enumerate(['First Name', 'Last Name', 'Gender', 'Date of Birth', 'Team', 'License', 'EMail']):
		ws.write( 0, c, f )
	
	xf = xlwt.easyxf( num_format_str='YYYY-MM-DD' )
	for r, rider in enumerate(riders):
		for c, a in enumerate(['first_name', 'last_name', 'gender', 'date_of_birth', 'team', 'license', 'email']):
			d = getattr(rider, a)
			if a == 'date_of_birth':
				ws.write( r+1, c, d, xf )
			else:
				ws.write( r+1, c, d )
	wb.save( response )
	return response
