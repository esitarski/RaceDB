import re
import os
import locale
import json
import datetime
import string

from . import utils
from .models import *
from .WriteLog import logCall

try:
	locale.setlocale(locale.LC_ALL, "")
except Exception as e:
	safe_print( u'Error: locale.setlocale(locale.LC_ALL, "") fails with "{}".'.format(e) )

from django.db.models import Q
from django.db import transaction, IntegrityError
from django.utils.text import format_lazy

try:
	from django.contrib.auth.views import logout
except:
	from django.contrib.auth import logout

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

from django import forms
from django.forms import ModelForm, Form
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django.utils import timezone

from django.templatetags.static import static

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button
from crispy_forms.layout import Fieldset, Field, MultiField, ButtonHolder
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, FieldWithButtons

from .autostrip import autostrip
from .context_processors import getContext

from django.views.decorators.cache import patch_cache_control

from functools import wraps
import inspect

#-----------------------------------------------------------------------

hub_mode = False
def set_hub_mode( hm = True ):
	global hub_mode
	hub_mode = hm
def get_hub_mode():
	return hub_mode
	
def access_validation( selfserve_ok=False, no_cache=True ):
	def decorator( decorated_func ):
		if not hub_mode:
			decorated_func = login_required(decorated_func)
		
		decorated_func = logCall(decorated_func)
		
		@wraps( decorated_func )
		def wrap( request, *args, **kwargs ):
			response = None
			if hub_mode and '/RaceDB/Hub' not in request.path:
				# If hub mode, default to hub search page.
				response = HttpResponseRedirect('/RaceDB/Hub/SearchCompetitions/')
			elif request.user.username == 'serve' and not selfserve_ok:
				# If self-serve, reject page that is not self-serve.
				response = HttpResponseRedirect('/RaceDB/SelfServe')
			elif not hub_mode and not request.user.is_superuser:
				# Unless superuser, cannot access a competition in the past.				
				competition = None
				if 'competitionId' in kwargs:
					competition = Competition.objects.filter(id=kwargs['competitionId']).first()
				elif 'participantId' in kwargs:
					participant = Participant.objects.filter(id=kwargs['participantId']).defer('signature').select_related('competition').first()
					if participant:
						competition = participant.competition
				elif 'eventId' in kwargs and 'eventType' in kwargs:
					try:
						eventType = int(kwargs['eventType'])
					except:
						eventType = -1
					if eventType == 0:
						event = EventMassStart.objects.filter(id=kwargs['eventId']).select_related('competition').first()
					elif eventType == 1:
						event = EventTT.objects.filter(id=kwargs['eventId']).select_related('competition').first()
					else:
						event = None
					if event:
						competition = event.competition
				
				if competition and competition.is_finished():
					response = HttpResponseRedirect('/RaceDB/PastCompetition')
							
			response = response or decorated_func( request, *args, **kwargs )
			
			if no_cache:
				patch_cache_control(
					response,
					no_cache=True,
					no_store=True,
					must_revalidate=True,
					proxy_revalidate=True,
					max_age=0,
				)
				response['Pragma'] = 'no-cache'
			return response
			
		return wrap
	return decorator
	
# Maximum return for large queries.
MaxReturn = 500

#-----------------------------------------------------------------------

def Container( *args ):
	return Div( *args, css_class = 'container' )

def Row( *args ):
	return Div( *args, css_class = 'row' )

def Col( field, cols=1 ):
	return Div( field, css_class = 'col-md-{}'.format(cols) )

def ColKey( *args, **kwargs ):
	return Div( *args, css_class = 'col-md-{}'.format(kwargs.get('cols',1)) )
	
def CancelButton( name=None, css_class=None, style=None ):
	return Button( 'cancel-button', name or _('Cancel'), css_class=css_class or 'btn btn-warning hidden-print', style=style or '', onclick='skip_back()' )

def CancelButton2( name=None, css_class=None, style=None ):
	return Button( 'cancel-button', name or _('Cancel'), css_class=css_class or 'btn btn-warning hidden-print', style=style or '', onclick='skip_back_n(2)' )

@autostrip
class SearchForm( Form ):
	search_text = forms.CharField( required = False )
	
	def __init__(self, additional_buttons, *args, **kwargs):
		self.additional_buttons = additional_buttons
		additional_buttons_on_new_row = kwargs.pop('additional_buttons_on_new_row', False)
		hide_cancel_button = kwargs.pop( 'hide_cancel_button', False )
		
		super(SearchForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', 'Search', css_class = 'btn btn-primary hidden-print' ),
		]
		
		Layout( Row( Col( Field('search_text', size=80), 6 ),) )
		
		# Add additional search buttons.
		for ab in additional_buttons:
			name, value, cls = ab[:3]
			if len(ab) == 4:
				button_args.append( Submit( name, value, css_class = cls + " hidden-print") )
				
		# Add cancel button.
		if not hide_cancel_button:
			button_args.append( CancelButton() )
			
		# Add non-search buttons.
		if additional_buttons:
			if additional_buttons_on_new_row:
				self.helper.layout.append( Row( *button_args ) )
				button_args = []
			else:
				button_args.append( HTML('&nbsp;' * 8) )
			for ab in additional_buttons:
				name, value, cls = ab[:3]
				if len(ab) == 3:
					button_args.append( Submit( name, value, css_class = cls + " hidden-print") )
		
		self.helper.layout.append(  HTML( '{{ form.errors }} {{ form.non_field_errors }}' ) )
		self.helper.layout.append( Row( *button_args ) )

#--------------------------------------------------------------------------------------------

SAVE_BUTTON		= (1<<0)
OK_BUTTON		= (1<<1)
CANCEL_BUTTON	= (1<<2)
NEW_BUTTONS		= OK_BUTTON | SAVE_BUTTON | CANCEL_BUTTON
SAVE_CANCEL_BUTTONS	= SAVE_BUTTON | CANCEL_BUTTON
DELETE_BUTTONS	= OK_BUTTON | CANCEL_BUTTON
EDIT_BUTTONS	= 0xFFFF

def addFormButtons( form, button_mask=EDIT_BUTTONS, additional_buttons=None, print_button=None, cancel_alias=None, additional_buttons_on_new_row=False ):
	btns = []
	if button_mask & SAVE_BUTTON:
		btns.append( Submit('save-submit', _('Save'), css_class='btn btn-primary hidden-print') )
	if button_mask & OK_BUTTON:
		btns.append( Submit('ok-submit', _('OK'), css_class='btn btn-primary hidden-print') )
	if button_mask & CANCEL_BUTTON:
		btns.append( CancelButton(cancel_alias) )
	
	if print_button:
		btns.append( HTML(u'&nbsp;' * 4) )
		btns.append( HTML(format_lazy( u'<button class="btn btn-primary hidden-print" onClick="window.print()">{}</button>', print_button) ) )
	
	if additional_buttons:
		if additional_buttons_on_new_row:
			form.helper.layout.append( Div(*btns, css_class='row') )
			btns = []
		else:
			btns.append( HTML(u'&nbsp;' * 4) )
		
		for i, ab in enumerate(additional_buttons):
			name, value, cls = ab[:3]
			btns.append( Submit(name, value, css_class = cls + ' hidden-print') )
			
	form.helper.layout.append( Div(*btns, css_class='row') )
		
	#form.helper.layout.append( Div( HTML( '{{ form.errors }} {{ form.non_field_errors }}' ), css_class = 'row') )

	
def GenericModelForm( ModelClass ):
	@autostrip
	class GMForm( ModelForm ):
		class Meta:
			model = ModelClass
			fields = '__all__'
			
		def __init__( self, *args, **kwargs ):
			self.button_mask = kwargs.pop( 'button_mask', [] )
			
			super(GMForm, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.additional_buttons = []
			addFormButtons( self, self.button_mask, self.additional_buttons )
			
	return GMForm

def GenericNew( ModelClass, request, ModelFormClass=None, template=None, additional_context={}, instance_fields={} ):
	title = format_lazy(u'{} {}', _('New'), ModelClass._meta.verbose_name)
	
	ModelFormClass = ModelFormClass or GenericModelForm(ModelClass)
	isEdit = False
	
	if request.method == 'POST':
		form = ModelFormClass( request.POST, button_mask=NEW_BUTTONS )
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, '{}Edit'.format(ModelClass.__name__), instance.id, cancelUrl=True) )
	else:
		instance = ModelClass( **instance_fields )
		form = ModelFormClass( instance=instance, button_mask=NEW_BUTTONS )
	
	form_context = {}
	form_context.update( locals() )
	form_context.update( additional_context )
	return render( request, template or 'generic_form.html', form_context )
	
def GenericEdit( ModelClass, request, instanceId, ModelFormClass=None, template=None, additional_context={},
		pre_edit_func=None, pre_save_func=None ):
	instance = get_object_or_404( ModelClass, pk=instanceId )
	if pre_edit_func:
		pre_edit_func( instance )
	
	ModelFormClass = ModelFormClass or GenericModelForm(ModelClass)
	isEdit = True
	
	title = format_lazy(u'{} {}', _('Edit'), ModelClass._meta.verbose_name)
	if request.method == 'POST':
		form = ModelFormClass( request.POST, button_mask=EDIT_BUTTONS, instance=instance )
		if form.is_valid():
			formInstance = form.save( commit = False )
			if pre_save_func:
				pre_save_func( formInstance )
			formInstance.save()
			try:
				form.save_m2m()
			except Exception as e:
				pass
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
			if 'save-submit' in request.POST:
				return HttpResponseRedirect('.')
				
			for ab in getattr(form, 'additional_buttons', []):
				if ab[3:] and ab[0] in request.POST:
					return ab[3]( request, instance )
	else:
		form = ModelFormClass( instance=instance, button_mask=EDIT_BUTTONS )
		
	form_context = {}
	form_context.update( locals() )
	form_context.update( additional_context )
	return render( request, template or 'generic_form.html', form_context )

def GenericDelete( ModelClass, request, instanceId, ModelFormClass = None, template = None, additional_context = {},
		pre_edit_func=None ):
	instance = get_object_or_404( ModelClass, pk=instanceId )
	
	ModelFormClass = ModelFormClass or GenericModelForm(ModelClass)
	isEdit = False
	
	title = format_lazy( u'{} {} ({})', _('Delete'), ModelClass._meta.verbose_name, _('are you sure? - there is no undo.') )
	if request.method == 'POST':
		instance.delete()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		if pre_edit_func:
			pre_edit_func( instance )
		form = setFormReadOnly( ModelFormClass(instance = instance, button_mask=DELETE_BUTTONS) )
		
	form_context = {}
	form_context.update( locals() )
	form_context.update( additional_context )
	return render( request, template or 'generic_form.html', form_context )

#-----------------------------------------------------------------------

@transaction.atomic
def NormalizeSequence( objs ):
	for sequence, o in enumerate(objs):
		o.sequence = sequence + 1
		o.save()
	
def SwapAdjacentSequence( Class, obj, swapBefore ):
	NormalizeSequence( Class.objects.all() )
	try:
		objAdjacent = Class.objects.get( sequence=obj.sequence + (-1 if swapBefore else 1) )
	except Class.DoesNotExist:
		return
		
	objAdjacent.sequence, obj.sequence = obj.sequence, objAdjacent.sequence
	objAdjacent.save()
	obj.save()

@transaction.atomic
def MoveSequence( Class, obj, toTop ):
	if toTop:
		for o in Class.objects.filter( sequence__lt = obj.sequence ):
			o.sequence = o.sequence + 1
			o.save()
		obj.sequence = 0
	else:
		for o in Class.objects.filter( sequence__gt = obj.sequence ):
			o.sequence = o.sequence - 1
			o.save()
		obj.sequence = Class.objects.count() - 1
	
	obj.save()	

#-----------------------------------------------------------------------

def pushUrl( request, name, *args, **kwargs ):
	cancelUrl = kwargs.pop( 'cancelUrl', False )
	while name.endswith('/'):
		name = name[:-1]
	target = getContext(request, 'cancelUrl' if cancelUrl else 'path')
	if args:
		url = u'{}{}/{}/'.format( target, name, u'/'.join( u'{}'.format(a) for a in args ) )
	else:
		url = u'{}{}/'.format( target, name )
	return url

def popPushUrl( request, name, *args, **kwargs ):
	kwargs['cancelUrl'] = True
	return pushUrl( request, name, *args, **kwargs )

def setFormReadOnly( form ):
	instance = getattr( form, 'instance', None )
	if instance:
		for name, field in form.fields.items():
			field.required = False
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

def applyFilter( query, objects, keyFunc = lambda x: u'{}'.format(x), doSort = True, reverse = False ):
	query = utils.normalizeSearch( query )
	if query:
		qFields = query.split()
		ret = (obj for obj in objects if all(q in utils.normalizeSearch(keyFunc(obj)) for q in qFields) )
	else:
		ret = objects
	if doSort:
		ret = sorted( ret, reverse = reverse, key = lambda obj: utils.normalizeSearch(keyFunc(obj)) )
	return ret
	
def copyFormFields( obj, form ):
	for f in form:
		setattr(obj, f.name, form.cleaned_data[f.name])
	return obj
	
def formChangedObject( obj_original, obj, form ):
	for f in form:
		if getattr(obj_original, f.name, None) != getattr(obj, f.name, None):
			return True
	return False

#-----------------------------------------------------------------------

def formatTime( secs, highPrecision = False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = secs % 60
	if highPrecision:
		secStr = '{:05.2f}'.format( secs + f )
	else:
		secStr = '{:02d}'.format( secs )
	
	if hours > 0:
		return "{}{}:{:02d}:{}".format(sign, hours, minutes, secStr)
	if minutes > 0:
		return "{}{}:{}".format(sign, minutes, secStr)
	return "{}{}".format(sign, secStr)
	
def formatTimeGap( secs, highPrecision = False ):
	if secs is None:
		secs = 0
	if secs < 0:
		sign = '-'
		secs = -secs
	else:
		sign = ''
	f, ss = math.modf(secs)
	secs = int(ss)
	hours = int(secs // (60*60))
	minutes = int( (secs // 60) % 60 )
	secs = secs % 60
	if highPrecision:
		decimal = '.{:02d}'.format(int(f * 100))
	else:
		decimal = ''
	if hours > 0:
		return "{}{}h{}'{:2d}{}\"".format(sign, hours, minutes, secs, decimal)
	else:
		return "{}{}'{:02d}{}\"".format(sign, minutes, secs, decimal)

def format_column_float( values ):
	values = list( values )
	if all( v is None or float(v) == int(v) for v in values ):
		return ['{}'.format(int(v)) if v is not None else None for v in values]
	elif all( v is None or float(v*10) == int(v*10) for v in values ):
		return ['{:.1f}'.format(v) if v is not None else None for v in values]
	else:
		return ['{:.2f}'.format(v) if v is not None else None for v in values]
	
def format_column_time( values ):
	return [None if v is None else formatTime(v) for v in values]
	
def format_column_gap( values ):
	return [None if v is None else formatTimeGap(v) for v in values]
