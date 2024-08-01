import re

from django.utils.translation import gettext_lazy as _

from .views_common import *
from .get_number_set_excel import get_number_set_excel
from .init_number_set import init_number_set

@autostrip
class NumberSetDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		btns = [('new-submit', _('New NumberSet'), 'btn btn-success')]
		addFormButtons( self, button_mask, btns )

@autostrip
class NumberSetForm( ModelForm ):
	class Meta:
		model = NumberSet
		fields = '__all__'
		
	def manageCB( self, request, numberSet ):
		return HttpResponseRedirect( pushUrl(request,'NumberSetManage', numberSet.id) )
		
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
			Row(
				Col(Field('range_str', size=80), 6),
			),
			Row(
				Col(Field('sponsor', size=80), 6),
			),
			Row(
				Col(Field('description', size=80), 6),
			),
			Field( 'sequence', type='hidden' ),
		)
		
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
					( 'manage-submit', _("Manage"), 'btn btn-primary', self.manageCB ),
			])
		
		addFormButtons( self, button_mask, self.additional_buttons )

@access_validation()
def NumberSetsDisplay( request ):
	NormalizeSequence( NumberSet.objects.all() )
	if request.method == 'POST':
	
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'NumberSetNew') )
			
		form = NumberSetDisplayForm( request.POST )
	else:
		form = NumberSetDisplayForm()
		
	number_sets = NumberSet.objects.all()
	return render( request, 'number_set_list.html', locals() )

@access_validation()
def NumberSetNew( request ):
	return GenericNew( NumberSet, request, NumberSetForm )

@access_validation()
def NumberSetDelete( request, numberSetId ):
	return GenericDelete( NumberSet, request, numberSetId, NumberSetForm )

@access_validation()
def NumberSetDown( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	SwapAdjacentSequence( NumberSet, number_set, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def NumberSetUp( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	SwapAdjacentSequence( NumberSet, number_set, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def NumberSetBottom( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	NormalizeSequence( NumberSet.objects.all() )
	MoveSequence( NumberSet, number_set, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def NumberSetTop( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	NormalizeSequence( NumberSet.objects.all() )
	MoveSequence( NumberSet, number_set, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def BibReturn( request, numberSetEntryId, confirmed=False ):
	nse = get_object_or_404( NumberSetEntry, pk=numberSetEntryId )
	if confirmed:
		nse.number_set.return_to_pool( nse.bib, nse.license_holder )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	page_title = _('Return Bib to NumberSet')
	message = format_lazy( '<strong>{}</strong>: {}<br/><br/>{}', nse.bib, nse.license_holder.full_name(), _('Return Bib to the NumberSet so it can be used again.') )
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'BibReturn/{}/{}/'.format(numberSetEntryId,1)
	return render( request, 'are_you_sure.html', locals() )

@access_validation()
def BibLost( request, numberSetEntryId, confirmed=False ):
	nse = get_object_or_404( NumberSetEntry, pk=numberSetEntryId )
	if confirmed:
		nse.date_lost = timezone.localtime(timezone.now()).date()
		nse.save()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	page_title = _('Record Bib as Lost (and unavailable)')
	message = format_lazy( '<strong>{}</strong>: {}<br/><br/>{}', nse.bib, nse.license_holder.full_name(), _('Record Bib as Lost and no longer available.') )
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'BibLost/{}/{}/'.format(numberSetEntryId,1)
	return render( request, 'are_you_sure.html', locals() )

@access_validation()
def NumberSetEdit( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	return GenericEdit( NumberSet, request, numberSetId, NumberSetForm )

@autostrip
class UploadNumberSetForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx)') )
	
	def __init__( self, *args, **kwargs ):
		super().__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xlsx"), 8),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_number_set( numberSetId, excel_contents ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO()
	init_number_set(
		numberSetId=numberSetId,
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
	)
	results_str = message_stream.getvalue()
	return results_str

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def UploadNumberSet( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	
	if request.method == 'POST':
		form = UploadNumberSetForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_number_set( numberSetId, request.FILES['excel_file'] )
			del request.FILES['excel_file']
			return render( request, 'upload_number_set.html', locals() )
	else:
		form = UploadNumberSetForm()
	
	return render( request, 'upload_number_set.html', locals() )
	
@autostrip
class NumberSetManageForm( Form ):
	search_text = forms.CharField( required=False, label=_("Search Text") )
	search_bib = forms.IntegerField( required=False, label=_("Search Bib"), min_value=1, max_value=999999 )
	
	def __init__( self, *args, **kwargs ):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('search_text', size=50), 4),
				Col(Field('search_bib', size=50), 4),
			),
		)
		
		self.additional_buttons = [
				( 'search-submit', _("Search"), 'btn btn-success' ),
				( 'ok-submit', _("OK"), 'btn btn-primary' ),
				( 'bib-list-update-submit', _("Update by Bib List"), 'btn btn-primary' ),
				( 'excel-export-submit', _("Export to Excel"), 'btn btn-primary' ),
				( 'excel-update-submit', _("Update from Excel"), 'btn btn-primary' ),
		]
		
		addFormButtons( self, 0, self.additional_buttons )

@access_validation()
def NumberSetManage( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	search_fields = request.session.get('number_set_manage_filter', {})
	
	number_set.validate()
	
	def getData( search_fields ):
		q = Q( number_set=number_set )
		
		search_bib = search_fields.get('search_bib', 0)
		if search_bib:
			q &= Q( bib=search_bib )
		
		search_text = utils.normalizeSearch( search_fields.get('search_text', '') )
		for n in search_text.split():
			q &= Q( license_holder__search_text__contains = n )
			
		return NumberSetEntry.objects.filter( q ).order_by( 'bib' )
	
	if request.method == 'POST':
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = NumberSetManageForm( request.POST )
		if form.is_valid():
			search_fields = {
				'search_text': form.cleaned_data['search_text'],
				'search_bib': form.cleaned_data['search_bib'],
			}
			request.session['number_set_manage_filter'] = search_fields
		
			if 'bib-list-update-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request,'NumberSetBibList', number_set.id) )
		
			if 'excel-export-submit' in request.POST:
				xl = get_number_set_excel( getData(search_fields) )
				response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
				response['Content-Disposition'] = 'attachment; filename=RaceDB-NumberSet-{}-{}.xlsx'.format(
					utils.cleanFileName(number_set.name),
					datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
				)
				return response
				
			if 'excel-update-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request,'NumberSetUploadExcel', number_set.id) )
	else:
		form = NumberSetManageForm( initial = search_fields )
	
	nses = getData( search_fields )
	return render( request, 'number_set_manage.html', locals() )	

@autostrip
class BibListForm( Form ):
	bibs = forms.CharField( required=False, label=_("Bib Numbers"), help_text=_("Comma separated list of bib numbers.") )
	
	def __init__( self, *args, **kwargs ):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('bibs', size=120), 8),
			),
		)
		
		self.additional_buttons = [
				( 'done-submit', _("Done"), 'btn btn-success' ),
				( 'lost-submit', _("Set Bibs Lost"), 'btn btn-primary' ),
				( 'found-submit', _("Set Bibs Found"), 'btn btn-primary' ),
		]
		
		addFormButtons( self, 0, self.additional_buttons )

@access_validation()
def NumberSetBibList( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	
	if request.method == 'POST':
		if 'done-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
		form = BibListForm( request.POST )
		if form.is_valid():
			bibs = form.cleaned_data['bibs']
			bibs = re.sub( r'\D+', ' ', bibs ).strip()
			bib_nums = set( int(n) for n in bibs.split() )
			
			if 'lost-submit' in request.POST:
				for bib in bib_nums:
					number_set.set_lost( bib )
			elif 'found-submit' in request.POST:
				for bib in bib_nums:
					number_set.return_to_pool( bib )
			
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = BibListForm()
	title = _('Number Set Bib List')
	return render( request, 'generic_form.html', locals() )	


