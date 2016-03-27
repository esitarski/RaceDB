from views_common import *
from django.utils.translation import ugettext_lazy as _

from get_number_set_excel import get_number_set_excel
from init_number_set import init_number_set

@autostrip
class NumberSetDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(NumberSetDisplayForm, self).__init__(*args, **kwargs)
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
		
		super(NumberSetForm, self).__init__(*args, **kwargs)
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
	return render_to_response( 'number_set_list.html', RequestContext(request, locals()) )

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
		nse.number_set.return_to_pool( nse.bib )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	page_title = _('Return Bib to NumberSet')
	message = string_concat('<strong>', unicode(nse.bib), u'</strong>: ', nse.license_holder.full_name(), u'<br/><br/>',
		_('Return Bib to the NumberSet so it can be used again.'))
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'BibReturn/{}/{}/'.format(numberSetEntryId,1)
	return render_to_response( 'are_you_sure.html', RequestContext(request, locals()) )

@access_validation()
def BibLost( request, numberSetEntryId, confirmed=False ):
	nse = get_object_or_404( NumberSetEntry, pk=numberSetEntryId )
	if confirmed:
		nse.number_set.return_to_pool( nse.bib )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	page_title = _('Record Bib as Lost (and unavailable)')
	message = string_concat('<strong>', unicode(nse.bib), u'</strong>: ', nse.license_holder.full_name(), u'<br/><br/>',
		_('Record Bib as Lost and no longer available.'))
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'BibLost/{}/{}/'.format(numberSetEntryId,1)
	return render_to_response( 'are_you_sure.html', RequestContext(request, locals()) )

@access_validation()
def NumberSetEdit( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	return GenericEdit( NumberSet, request, numberSetId, NumberSetForm )

@autostrip
class UploadNumberSetForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx, *.xls)') )
	
	def __init__( self, *args, **kwargs ):
		super( UploadNumberSetForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xls,.xlsx"), 8),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_number_set( numberSetId, excel_contents ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO.StringIO()
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
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = UploadNumberSetForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_number_set( numberSetId, request.FILES['excel_file'] )
			del request.FILES['excel_file']
			return render_to_response( 'upload_number_set.html', RequestContext(request, locals()) )
	else:
		form = UploadNumberSetForm()
	
	return render_to_response( 'upload_number_set.html', RequestContext(request, locals()) )
	
@autostrip
class NumberSetManageForm( Form ):
	search_text = forms.CharField( required=False, label=_("Search Text") )
	search_bib = forms.IntegerField( required=False, label=_("Search Bib"), min_value=1, max_value=999999 )
	
	def __init__( self, *args, **kwargs ):
		super(NumberSetManageForm, self).__init__(*args, **kwargs)
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
				( 'excel-export-submit', _("Export to Excel"), 'btn btn-primary' ),
				( 'excel-update-submit', _("Update from Excel"), 'btn btn-primary' ),
		]
		
		addFormButtons( self, 0, self.additional_buttons )

@access_validation()
def NumberSetManage( request, numberSetId ):
	number_set = get_object_or_404( NumberSet, pk=numberSetId )
	search_fields = request.session.get('number_set_manage_filter', {})
	
	number_set.normalize()
	
	def getData( search_fields ):
		q = Q()
		
		search_text = utils.normalizeSearch( search_fields.get('search_text', '') )
		for n in search_text.split():
			q &= Q( license_holder__search_text__contains = n )
			
		search_bib = search_fields.get('search_bib', 0)
		if search_bib:
			q &= Q( bib=search_bib )
		
		license_holders = defaultdict( list )
		
		for nse in NumberSetEntry.objects.select_related('license_holder').filter(number_set=number_set, date_lost=None).filter(q).order_by('bib'):
			license_holders[nse.license_holder].append( nse )
		for lh, nses in license_holders.iteritems():
			lh.nses = nses
		license_holders = sorted( (license_holders.iterkeys()), key = lambda lh: lh.search_text )
		number_set_lost = NumberSetEntry.objects.select_related('license_holder').filter(number_set=number_set).exclude(date_lost=None).filter(q).order_by('bib')
		
		return license_holders, number_set_lost
	
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
		
			if 'excel-export-submit' in request.POST:
				xl = get_number_set_excel( *getData(search_fields) )
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
	
	license_holders, number_set_lost = getData( search_fields )
	allocated_bibs_count = sum( len(lh.nses) for lh in license_holders )
	return render_to_response( 'number_set_manage.html', RequestContext(request, locals()) )	


