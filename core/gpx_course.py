import io

from django.utils.translation import gettext_lazy as _

from .views_common import *
from .gpx_util import simplify_gpx_file

gpx_fields = ('name', 'description', 'is_loop')

#-----------------------------------------------------------------------
@autostrip
class GPXCourseForm( Form ):
	name = forms.CharField( max_length=32, label=_('Name') )
	description = forms.CharField( max_length=160, required=False, label=_('Description') )
	is_loop = forms.BooleanField( required=False, label=_('Is Loop') )
	gpx_file = forms.FileField( required=False, label=_('GPX File (*.gpx)') )
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('name', size=32),
			),
			Row(
				Field('description', size=80),
			),
			Row(
				Field('is_loop'),
			),
			Row(
				Field('gpx_file'),
			),
		)
		addFormButtons( self, button_mask )

@access_validation()
def GPXCourses( request ):	
	gpx_courses = GPXCourse.objects.all()
	return render( request, 'gpx_course_list.html', locals() )
	
def read_gpx( f ):
	lat_lon_elevation = simplify_gpx_file( io.StringIO(f.read().decode('utf8')) )[0]
	return lat_lon_elevation

@access_validation()
def GPXCourseNew( request ):
	title = format_lazy('{} {}', _('New'), GPXCourse._meta.verbose_name)
	
	if request.method == 'POST':
		form = GPXCourseForm( request.POST, request.FILES, button_mask=NEW_BUTTONS )
		if form.is_valid():
			initial = {f:form.cleaned_data[f] for f in gpx_fields}
			initial['lat_lon_elevation'] = read_gpx( request.FILES['gpx_file'] )
			instance = GPXCourse( **initial )
			instance.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'GPXCourseEdit', instance.id, cancelUrl=True) )
	else:
		initial={'lat_lon_elevation':[],'is_loop': True, 'meters':0.0}
		form = GPXCourseForm( initial=initial, button_mask=NEW_BUTTONS )
	
	return render( request, 'gpx_course_form.html', locals() )

@access_validation()
def GPXCourseEdit( request, gpxCourseId ):
	gpx_course = get_object_or_404( GPXCourse, pk=gpxCourseId )
	
	if request.method == 'POST':
		form = GPXCourseForm( request.POST, request.FILES, button_mask=EDIT_BUTTONS )
		if form.is_valid():
			for f in gpx_fields:
				setattr( gpx_course, f, form.cleaned_data[f] )
			gpx_course.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect( getContext(request,'cancelUrl') )
				
	initial = {f:getattr(gpx_course, f) for f in gpx_fields}
	form = GPXCourseForm( initial=initial, button_mask=EDIT_BUTTONS )
	initial['lat_lon_elevation'] = gpx_course.lat_lon_elevation
	initial['meters'] = gpx_course.meters
	
	return render( request, 'gpx_course_form.html', locals() )

@access_validation()
def GPXCourseDelete( request, gpxCourseId, confirmed=0 ):
	gpx_course = get_object_or_404( GPXCourse, pk=gpxCourseId )
	if int(confirmed):
		gpx_course.delete()
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	message = format_lazy( '{}: {}, {}', _('Delete'), gpx_course.name, gpx_course.description )
	cancel_target = getContext(request,'cancelUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )

