import uuid
from subprocess import Popen, PIPE
import traceback
import operator

from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .views_common import *

#-----------------------------------------------------------------------
@autostrip
class ImageForm( ModelForm ):
	class Meta:
		model = Image
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('title', size=32),
			),
			Row(
				Field('description', size=80),
			),
			Row(
				Field('image'),
			),
		)
		addFormButtons( self, button_mask )

@access_validation()
def Images( request ):	
	images = Image.objects.all()
	return render( request, 'image_list.html', locals() )

@access_validation()
def ImageNew( request ):
	title = format_lazy('{} {}', _('New'), Image._meta.verbose_name)
	
	if request.method == 'POST':
		form = ImageForm( request.POST, request.FILES, button_mask=NEW_BUTTONS )
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, '{}Edit'.format(ModelClass.__name__), instance.id, cancelUrl=True) )
	else:
		instance = Image()
		form = ImageFormClass( instance=instance, button_mask=NEW_BUTTONS )
	
	return render( request, template or 'generic_form.html', locals() )

@access_validation()
def ImageEdit( request, imageId ):
	image = get_object_or_404( Image, pk=imageId )
	
	if request.method == 'POST':
		form = ImageForm( request.POST, request.FILES, instance=image, button_mask=EDIT_BUTTONS )
		if form.is_valid():
			form.save()
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect( getContext(request,'cancelUrl') )
	else:
		form = ImageForm( instance=image, button_mask=EDIT_BUTTONS )
	
	return GenericEdit( Image, request, image.id, ImageForm, 'image_form.html', locals() )

@access_validation()
def ImageDelete( request, imageId, confirmed=0 ):
	image = get_object_or_404( Image, pk=imageId )
	if int(confirmed):
		image.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( '{}: {}, {}', _('Delete'), image.name, image.description )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

