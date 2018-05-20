from views_common import *
from django.utils.translation import ugettext_lazy as _
from views import license_holders_from_search_text
from get_seasons_pass_excel import get_seasons_pass_excel
from init_seasons_pass import init_seasons_pass

@autostrip
class SeasonsPassDisplayForm( Form ):
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(SeasonsPassDisplayForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		btns = [('new-submit', _("New Season's Pass"), 'btn btn-success')]
		addFormButtons( self, button_mask, btns )

@autostrip
class SeasonsPassForm( ModelForm ):
	class Meta:
		model = SeasonsPass
		fields = '__all__'
		
	def addSeasonsPassHolderDB( self, request, seasonsPass ):
		return HttpResponseRedirect( pushUrl(request, 'SeasonsPassHolderAdd', seasonsPass.id) )
		
	def exportToExcelCB( self, request, seasonsPass ):
		xl = get_seasons_pass_excel( seasonsPass )
		response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
		response['Content-Disposition'] = 'attachment; filename=RaceDB-SeasonsPassHolders-{}-{}.xlsx'.format(
			utils.cleanFileName(seasonsPass.name),
			datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
		)
		return response
		
	def importFromExcelCB( self, request, seasonsPass ):
		return HttpResponseRedirect( pushUrl(request, 'SeasonsPassHolderUploadExcel', seasonsPass.id) )		
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', OK_BUTTON )
		
		super(SeasonsPassForm, self).__init__(*args, **kwargs)
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
					( 'add-seasons-pass-holder-submit', _("Add Season's Pass Holders"), 'btn btn-success', self.addSeasonsPassHolderDB ),
					( 'excel-import-submit', _("Import from Excel"), 'btn btn-primary', self.importFromExcelCB ),
					( 'excel-export-submit', _("Export to Excel"), 'btn btn-primary', self.exportToExcelCB ),
			])
		
		addFormButtons( self, button_mask, self.additional_buttons )

@access_validation()
def SeasonsPassesDisplay( request ):
	NormalizeSequence( SeasonsPass.objects.all() )
	if request.method == 'POST':
	
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'SeasonsPassNew') )
			
		form = SeasonsPassDisplayForm( request.POST )
	else:
		form = SeasonsPassDisplayForm()
	
	seasons_passes = SeasonsPass.objects.all()
	return render( request, 'seasons_pass_list.html', locals() )

@access_validation()
def SeasonsPassNew( request ):
	return GenericNew( SeasonsPass, request, SeasonsPassForm )

@access_validation()
def SeasonsPassEdit( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	return GenericEdit(
		SeasonsPass, request, seasonsPassId, SeasonsPassForm,
		template='seasons_pass_edit.html',
		additional_context={'seasons_pass_entries':SeasonsPassHolder.objects.select_related('license_holder').filter(seasons_pass=seasons_pass)}
	)
	
@access_validation()
def SeasonsPassDelete( request, seasonsPassId ):
	return GenericDelete( SeasonsPass, request, seasonsPassId, SeasonsPassForm )

@access_validation()
def SeasonsPassCopy( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	seasons_pass.clone()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def SeasonsPassDown( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	SwapAdjacentSequence( SeasonsPass, seasons_pass, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def SeasonsPassUp( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	SwapAdjacentSequence( SeasonsPass, seasons_pass, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def SeasonsPassBottom( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	NormalizeSequence( SeasonsPass.objects.all() )
	MoveSequence( SeasonsPass, seasons_pass, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def SeasonsPassTop( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	NormalizeSequence( SeasonsPass.objects.all() )
	MoveSequence( SeasonsPass, seasons_pass, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#--------------------------------------------------------------------------------------------

@access_validation()
def SeasonsPassHolderAdd( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	
	search_text = request.session.get('license_holder_filter', '')
	btns = [
		('license-holder-new-submit', _('Create New License Holder'), 'btn btn-warning'),
		('ok-submit', _('OK'), 'btn btn-success'),
	]
	if request.method == 'POST':
	
		if 'ok-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'license-holder-new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderNew') )
			
		form = SearchForm( btns, request.POST, hide_cancel_button=True )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['license_holder_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text}, hide_cancel_button=True )
	
	existing_seasons_pass_holders = set(spe.license_holder.id for spe in SeasonsPassHolder.objects.filter(seasons_pass=seasons_pass))
	
	# Analyse the search_text to try to use an indexed field.
	search_text = utils.normalizeSearch(search_text)
	license_holders = license_holders_from_search_text( search_text )
	return render( request, 'license_holder_seasons_pass_list.html', locals() )

@access_validation()
def SeasonsPassLicenseHolderAdd( request, seasonsPassId, licenseHolderId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	try:
		SeasonsPassHolder( seasons_pass=seasons_pass, license_holder=license_holder ).save()
	except Exception as e:
		safe_print( e )
		pass
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def SeasonsPassLicenseHolderRemove( request, seasonsPassId, licenseHolderId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	try:
		SeasonsPassHolder.objects.get( seasons_pass=seasons_pass, license_holder=license_holder ).delete()
	except Exception as e:
		safe_print( e )
		pass
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
def SeasonsPassHolderRemove( request, seasonsPassHolderId ):
	seasons_pass_holder = get_object_or_404( SeasonsPassHolder, pk=seasonsPassHolderId )
	seasons_pass_holder.delete()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------
@autostrip
class UploadSeasonsPassForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx, *.xls)') )
	clear_existing = forms.BooleanField( required=False, label=_('Clear Existing Seasons Pass Holders First'), help_text=_("Removes all current Season's Pass Holders.  Use with Caution.") )
	
	def __init__( self, *args, **kwargs ):
		super( UploadSeasonsPassForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xls,.xlsx"), 8),
				Col( Field('clear_existing'), 4 ),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_seasons_pass( seasonsPassId, excel_contents, clear_existing ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO()
	init_seasons_pass(
		seasonsPassId=seasonsPassId,
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
		clear_existing=clear_existing,
	)
	results_str = message_stream.getvalue()
	return results_str

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def UploadSeasonsPass( request, seasonsPassId ):
	seasons_pass = get_object_or_404( SeasonsPass, pk=seasonsPassId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = UploadSeasonsPassForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_seasons_pass( seasonsPassId, request.FILES['excel_file'], form.cleaned_data['clear_existing'] )
			del request.FILES['excel_file']
			return render( request, 'upload_seasons_pass.html', locals() )
	else:
		form = UploadSeasonsPassForm()
	
	return render( request, 'upload_seasons_pass.html', locals() )


