import io

from django.utils.translation import gettext_lazy as _

from .views_common import *
from .init_categories import read_categories, get_category_excel
from .FieldMap import standard_field_map
from .utils import sanitize_windows_filename

@autostrip
class CategoryFormatForm( ModelForm ):
	class Meta:
		model = CategoryFormat
		fields = '__all__'
		
	def newCategoryCB( self, request, categoryFormat ):
		return HttpResponseRedirect( pushUrl(request, 'CategoryNew', categoryFormat.id) )
		
	def importFromExcelCB( self, request, categoryFormat ):
		return HttpResponseRedirect( pushUrl(request, 'UploadCategoryFormat', categoryFormat.id) )
	
	def exportToExcelCB( self, request, categoryFormat ):
		return HttpResponseRedirect( pushUrl(request, 'ExportCategoryFormat', categoryFormat.id) )
	
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', EDIT_BUTTONS )
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('name', size=50), 4),
				Col(Field('description', size=100), 8),
			),
		)
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
				( 'new-category-submit', _('New Category'), 'btn btn-success', self.newCategoryCB ),
				( 'immport_from-excel-submit', _('Upload From Excel'), 'btn btn-primart', self.importFromExcelCB ),
				( 'export_to-excel-submit', _('Export to Excel'), 'btn btn-primart', self.exportToExcelCB ),
			])
			
		addFormButtons( self, button_mask, self.additional_buttons )
		
def CategoryFormatsDisplay( request ):
	search_text = request.session.get('categoryFormat_filter', '')
	btns = [('new-submit', _('New Category Format'), 'btn btn-success')]
	
	if request.method == 'POST':
	
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'CategoryFormatNew') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['categoryFormat_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
		
	category_formats = applyFilter( search_text, CategoryFormat.objects.all(), CategoryFormat.get_search_text )
	return render( request, 'category_format_list.html', locals() )

@access_validation()
def CategoryFormatNew( request ):
	return GenericNew( CategoryFormat, request, CategoryFormatForm, template = 'category_format_form.html' )

@access_validation()
def CategoryFormatEdit( request, categoryFormatId ):
	return GenericEdit( CategoryFormat, request, categoryFormatId, CategoryFormatForm, template = 'category_format_form.html' )
	
@access_validation()
def CategoryFormatCopy( request, categoryFormatId ):
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )
	category_format_new = category_format.make_copy()
	category_format_new.name = getCopyName( CategoryFormat, category_format.name )
	category_format.save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryFormatDelete( request, categoryFormatId ):
	return GenericDelete( CategoryFormat, request, categoryFormatId, template = 'category_format_form.html' )

@transaction.atomic
def CategorySwapAdjacent( category, swapBefore ):
	NormalizeSequence( Category.objects.filter(format=category.format) )
	try:
		categoryAdjacent = Category.objects.get(format=category.format, sequence=category.sequence + (-1 if swapBefore else 1) )
	except Category.DoesNotExist:
		return
		
	categoryAdjacent.sequence, category.sequence = category.sequence, categoryAdjacent.sequence
	categoryAdjacent.save()
	category.save()

#--------------------------------------------------------------------------------------------

@autostrip
class CategoryForm( ModelForm ):
	class Meta:
		model = Category
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('code', size=32),
				Field('gender'),
				Field('description', size=80),
			),
			Row(
				Col(Field('aliases', size=160), 12),
			),
			Field( 'sequence', type='hidden' ),
			Field( 'format', type='hidden' ),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryNew( request, categoryFormatId ):
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )

	title = '{} {}'.format(_('New'), Category._meta.verbose_name.title())
	
	if request.method == 'POST':
		form = CategoryForm( request.POST )
		if form.is_valid():
			category = form.save( commit = False )
			category.format = category_format
			category.sequence = category_format.next_category_seq
			category.save()
			
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request,'CategoryEdit', category.id, cancelUrl = True) )
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		category = Category( format = category_format ,sequence = 0 )
		form = CategoryForm( instance = category )
	
	return render( request, 'category_form.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryEdit( request, categoryId ):
	return GenericEdit( Category, request, categoryId, CategoryForm, template = 'category_form.html' )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryDelete( request, categoryId ):
	return GenericDelete( Category, request, categoryId, CategoryForm )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategorySequence( request, categoryId, sequence ):
	category = get_object_or_404( Category, pk=categoryId )
	
	elements = list( category.format.category_set.all() )
	i_new = max( 0, min( int(sequence)-1, len(elements)-1 ) )
	elements.remove( category )
	elements.insert( i_new, category )
	category.sequence = -1
	validate_sequence( elements )
	return HttpResponseRedirect( getContext(request, 'cancelUrl') )
	
#-----------------------------------------------------------------------

@autostrip
class UploadCategoryFormatForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx)') )
	clear_contents = forms.BooleanField( required=False, label=_('Clear Existing Categories') )
	
	def __init__( self, *args, **kwargs ):
		super().__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xlsx"), 8),
			),
			Row(
				Col( Field('clear_contents', accept=".xlsx"), 8),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_category_format( categoryFormatId, excel_contents, clear_contents=False ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO()
	read_categories(
		categoryFormatId=categoryFormatId,
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
		clear_contents=clear_contents,
	)
	results_str = message_stream.getvalue()
	return results_str

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def UploadCategoryFormat( request, categoryFormatId ):
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )

	if request.method == 'POST':
		form = UploadCategoryFormatForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_category_format( categoryFormatId, request.FILES['excel_file'], clear_contents=form.cleaned_data['clear_contents'] )
	else:
		form = UploadCategoryFormatForm()
	
	ifm = standard_field_map()
	column_info = [(f, ifm.get_aliases(f), optional, ifm.get_description(f))
		for f, optional in (('category_format', True), ('aliases', True), ('gender', True), ('description', True))
	]

	categories = category_format.category_set.all()
	return render( request, 'upload_category_format.html', locals() )


@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def ExportCategoryFormat( request, categoryFormatId ):
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )
	
	wb = get_category_excel( category_format )
	buffer = io.BytesIO()
	wb.save( buffer )
	buffer.seek( 0 )
	response = HttpResponse(
		buffer.read(),
		content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	)
	now_str = timezone.now().strftime("%Y-%m-%dT%H%M%S")
	fname = sanitize_windows_filename( f'{category_format.name}-{now_str}' ) + '.xlsx'
	response["Content-Disposition"] = f'attachment; filename="{fname}"'
	return response
