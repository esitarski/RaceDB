from views_common import *
from django.utils.translation import ugettext_lazy as _

def GetCategoryNumbersForm( competition, category_numbers = None ):
	class CategoryNumbersForm( GenericModelForm(CategoryNumbers) ):
		def __init__( self, *args, **kwargs ):
			super(CategoryNumbersForm, self).__init__(*args, **kwargs)
			categories_field = self.fields['categories']
			
			category_list = competition.get_categories_without_numbers()
			
			if category_numbers is not None:
				category_list.extend( category_numbers.get_category_list() )
				category_list.sort( key = lambda c: c.sequence )
				
			categories_field.choices = [(category.id, category.full_name()) for category in category_list]
			categories_field.label = _('Available Categories')
			self.helper['categories'].wrap( Field, size=12 )
			self.helper['competition'].wrap( Field, type='hidden' )
	return CategoryNumbersForm
		
@access_validation()
def CategoryNumbersDisplay( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	category_numbers_list = sorted( CategoryNumbers.objects.filter(competition = competition), key = CategoryNumbers.get_key )
	return render( request, 'category_numbers_list.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryNumbersNew( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	category_numbers_list = CategoryNumbers.objects.filter( competition = competition )

	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = GetCategoryNumbersForm(competition)(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request,'CategoryNumbersEdit', instance.id, cancelUrl = True) )
	else:
		category_numbers = CategoryNumbers()
		category_numbers.competition = competition
		form = GetCategoryNumbersForm(competition)( instance = category_numbers, button_mask = NEW_BUTTONS )
	
	return render( request, 'category_numbers_form.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryNumbersEdit( request, categoryNumbersId ):
	category_numbers = get_object_or_404( CategoryNumbers, pk=categoryNumbersId )
	competition = category_numbers.competition
	return GenericEdit(
		CategoryNumbers, request, categoryNumbersId,
		GetCategoryNumbersForm(competition, category_numbers),
		template = 'category_numbers_form.html',
		additional_context = dict(
			competition = competition,
			category_numbers_list = CategoryNumbers.objects.filter( competition = competition )
		),
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CategoryNumbersDelete( request, categoryNumbersId ):
	category_numbers = get_object_or_404( CategoryNumbers, pk=categoryNumbersId )
	competition = category_numbers.competition
	category_numbers_list = CategoryNumbers.objects.filter( competition = competition )
	return GenericDelete(
		CategoryNumbers, request, categoryNumbersId,
		GetCategoryNumbersForm(competition, category_numbers),
		template = 'category_numbers_form.html',
		additional_context = dict(
			competition = competition,
			category_numbers_list = CategoryNumbers.objects.filter( competition = competition )
		),
	)

