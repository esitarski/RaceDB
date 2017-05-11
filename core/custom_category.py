import operator
from collections import defaultdict

from views_common import *
from django.utils.translation import ugettext_lazy as _

def GetCustomCategoryForm( cls ):
	@autostrip
	class CustomCategoryForm( ModelForm ):
		class Meta:
			model = cls
			fields = '__all__'
			
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
			
			super(CustomCategoryForm, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.helper.layout = Layout(
				Row(
					Field('name', size=60),
				),
				Row(
					Field('range_str', size=60),
				),
				Row(
					Col( Field('gender'), 3),
					Col( Field('date_of_birth_minimum'), 3),
					Col( Field('date_of_birth_maximum'), 3),
				),
				Row(
					Col( Field('nation_code_str', size=30), 3),
					Col( Field('state_prov_str', size=30), 3),
					Col( Field('license_code_prefixes', size=30), 3),
				),
				Field('event', type='hidden'),
				Field('sequence', type='hidden'),
			)

			addFormButtons( self, button_mask )
	return CustomCategoryForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CustomCategoryNew( request, eventId, eventType ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart, EventTT)[eventType], pk=eventId )
	CCC = event.get_custom_category_class()
	return GenericNew(
		CCC, request, GetCustomCategoryForm(CCC),
		instance_fields=dict(event=event, name=datetime.datetime.now().strftime('Custom Category %Y-%m-%d %H:%M:%S'))
	)

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CustomCategoryEdit( request, eventId, eventType, customCategoryId ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart, EventTT)[eventType], pk=eventId )
	CCC = event.get_custom_category_class()
	custom_category = get_object_or_404( CCC, pk=customCategoryId )
	custom_category.validate_sequence()
	return GenericEdit( CCC, request,
		customCategoryId,
		GetCustomCategoryForm(CCC),
	)	

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CustomCategoryMassStartEdit( request, customCategoryId ):
	return GenericEdit( CustomCategoryMassStart, request,
		customCategoryId,
		GetCustomCategoryForm(CustomCategoryMassStart),
	)	

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CustomCategoryTTEdit( request, customCategoryId ):
	return GenericEdit( CustomCategoryTT, request,
		customCategoryId,
		GetCustomCategoryForm(CustomCategoryTT),
	)	

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CustomCategoryDelete( request, eventId, eventType, customCategoryId, confirmed=0 ):
	eventType = int(eventType)
	event = get_object_or_404( (EventMassStart, EventTT)[eventType], pk=eventId )
	CCC = event.get_custom_category_class()
	custom_category = get_object_or_404( CCC, pk=customCategoryId )
	if int(confirmed):
		custom_category.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = string_concat( _('Delete: '), custom_category.name )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )
