from views_common import *
from django.utils.translation import ugettext_lazy as _

@autostrip
class CategoryFormatForm( ModelForm ):
	class Meta:
		model = CategoryFormat
		fields = '__all__'
		
	def newCategoryCB( self, request, categoryFormat ):
		return HttpResponseRedirect( pushUrl(request, 'CategoryNew', categoryFormat.id) )
	
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop( 'button_mask', EDIT_BUTTONS )
		
		super(CategoryFormatForm, self).__init__(*args, **kwargs)
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
			])
			
		addFormButtons( self, button_mask, self.additional_buttons )
		
def CategoryFormatsDisplay( request ):
	search_text = request.session.get('categoryFormat_filter', '')
	btns = [('new-submit', _('New Category'), 'btn btn-success')]
	
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
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
		
		super(CategoryForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('code', size=20),
				Field('gender'),
				Field('description', size=80),
			),
			Field( 'sequence', type='hidden' ),
			Field( 'format', type='hidden' ),
		)
		addFormButtons( self, button_mask )

		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryNew( request, categoryFormatId ):
	category_format = get_object_or_404( CategoryFormat, pk=categoryFormatId )

	title = unicode(_('New {}')).format(Category._meta.verbose_name.title())
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
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


