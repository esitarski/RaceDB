from django.db.models import Q
from django.db import transaction

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.forms import ModelForm, Form
from django.forms.models import inlineformset_factory
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, MultiField, ButtonHolder, Div, Submit

from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions

SAVE_BUTTON		= (1<<0)
OK_BUTTON		= (1<<1)
CANCEL_BUTTON	= (1<<2)
NEW_BUTTONS		= OK_BUTTON | SAVE_BUTTON | CANCEL_BUTTON
DELETE_BUTTONS	= OK_BUTTON | CANCEL_BUTTON
EDIT_BUTTONS	= 0xFFFF

def addFormButtons( form, button_mask = EDIT_BUTTONS, additional_buttons = [] ):
	btns = []
	if button_mask & SAVE_BUTTON != 0:
		btns.append( Submit('save-submit', _('Save'), css_class='btn btn-primary') )
	if button_mask & OK_BUTTON:
		btns.append( Submit('ok-submit', _('OK'), css_class='btn btn-primary') )
	if button_mask & CANCEL_BUTTON:
		btns.append( Submit('cancel-submit', _('Cancel'), css_class='btn btn-warning') )
		
	if additional_buttons:
		btns.append( HTML('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;') )
		
	for ab in additional_buttons:
		name, value, cls = ab[:3]
		btns.append( Submit( name, value, css_class = cls ) )
		
	form.helper.layout.append( Div(*btns, css_class = 'row') )
	form.helper.layout.append( Div( HTML( '{{ form.errors }} {{ form.non_field_errors }}' ), css_class = 'row') )


def CreateGeneric( ModelClass, ModelFormClass ):
	modelClassName = ModelClass.__name__

	class ModelForm( ModelForm ):
		class Meta:
			model = ModelClass
			
		def __init__( self, *args, **kwargs ):
			self.button_mask = kwargs.pop( 'button_mask', [] )
			
			super(Form, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.additional_buttons = []
			addFormButtons( self, self.button_mask, self.additional_buttons )
			
	return {}

