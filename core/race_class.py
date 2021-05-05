from django.utils.translation import gettext_lazy as _

from .views_common import *

@autostrip
class RaceClassDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		btns = [('new-submit', _('New Race Class'), 'btn btn-success')]
		addFormButtons( self, button_mask, btns )

@autostrip
class RaceClassForm( ModelForm ):
	class Meta:
		model = RaceClass
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('name', size=50), 4),
			),
			Field( 'sequence', type='hidden' ),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
def RaceClassesDisplay( request ):
	NormalizeSequence( RaceClass.objects.all() )
	if request.method == 'POST':
	
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'RaceClassNew') )
			
		form = RaceClassDisplayForm( request.POST )
	else:
		form = RaceClassDisplayForm()
		
	race_classes = RaceClass.objects.all()
	return render( request, 'race_class_list.html', locals() )

@access_validation()
def RaceClassNew( request ):
	return GenericNew( RaceClass, request, RaceClassForm )

@access_validation()
def RaceClassEdit( request, raceClassId ):
	return GenericEdit( RaceClass, request, raceClassId, RaceClassForm )
	
@access_validation()
def RaceClassDelete( request, raceClassId ):
	return GenericDelete( RaceClass, request, raceClassId, RaceClassForm )

@access_validation()
def RaceClassDown( request, raceClassId ):
	raceClass = get_object_or_404( RaceClass, pk=raceClassId )
	SwapAdjacentSequence( RaceClass, raceClass, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def RaceClassUp( request, raceClassId ):
	raceClass = get_object_or_404( RaceClass, pk=raceClassId )
	SwapAdjacentSequence( RaceClass, raceClass, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def RaceClassBottom( request, raceClassId ):
	raceClass = get_object_or_404( RaceClass, pk=raceClassId )
	NormalizeSequence( RaceClass.objects.all() )
	MoveSequence( RaceClass, raceClass, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def RaceClassTop( request, raceClassId ):
	raceClass = get_object_or_404( RaceClass, pk=raceClassId )
	NormalizeSequence( RaceClass.objects.all() )
	MoveSequence( RaceClass, raceClass, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
