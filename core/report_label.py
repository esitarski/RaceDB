from views_common import *
from django.utils.translation import ugettext_lazy as _

@autostrip
class ReportLabelDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(ReportLabelDisplayForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		btns = [('new-submit', _('New ReportLabel'), 'btn btn-success')]
		addFormButtons( self, button_mask, btns )

@autostrip
class ReportLabelForm( ModelForm ):
	class Meta:
		model = ReportLabel
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(ReportLabelForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('name', size=50), 4),
			),
			Field( 'sequence', type='hidden' ),
		)
		
		self.additional_buttons = []
		
		addFormButtons( self, button_mask, self.additional_buttons )

@access_validation()
def ReportLabelsDisplay( request ):
	NormalizeSequence( ReportLabel.objects.all() )
	if request.method == 'POST':
	
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'ReportLabelNew') )
			
		form = ReportLabelDisplayForm( request.POST )
	else:
		form = ReportLabelDisplayForm()
		
	report_labels = ReportLabel.objects.all()
	return render( request, 'report_label_list.html', locals() )

@access_validation()
def ReportLabelNew( request ):
	return GenericNew( ReportLabel, request, ReportLabelForm )

@access_validation()
def ReportLabelEdit( request, reportLabelId ):
	report_label = get_object_or_404( ReportLabel, pk=reportLabelId )
	return GenericEdit(
		ReportLabel, request, reportLabelId, ReportLabelForm,
	)
	
@access_validation()
def ReportLabelDelete( request, reportLabelId ):
	return GenericDelete( ReportLabel, request, reportLabelId, ReportLabelForm )

@access_validation()
def ReportLabelDown( request, reportLabelId ):
	report_label = get_object_or_404( ReportLabel, pk=reportLabelId )
	SwapAdjacentSequence( ReportLabel, report_label, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def ReportLabelUp( request, reportLabelId ):
	report_label = get_object_or_404( ReportLabel, pk=reportLabelId )
	SwapAdjacentSequence( ReportLabel, report_label, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def ReportLabelBottom( request, reportLabelId ):
	report_label = get_object_or_404( ReportLabel, pk=reportLabelId )
	NormalizeSequence( ReportLabel.objects.all() )
	MoveSequence( ReportLabel, report_label, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def ReportLabelTop( request, reportLabelId ):
	report_label = get_object_or_404( ReportLabel, pk=reportLabelId )
	NormalizeSequence( ReportLabel.objects.all() )
	MoveSequence( ReportLabel, report_label, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
