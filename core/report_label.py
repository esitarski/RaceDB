from django.utils.translation import gettext_lazy as _

from .views_common import *

@autostrip
class ReportLabelDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
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

