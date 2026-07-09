from django.utils.translation import gettext_lazy as _

from .views_common import *

def GetCategoryNumbersForm( competition, category_numbers=None ):
	
	class CategoryNumbersForm( GenericModelForm(CategoryNumbers) ):
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop( 'button_mask', EDIT_BUTTONS )
			
			super().__init__(*args, **kwargs)
			categories_field = self.fields['categories']
			
			category_list = competition.get_categories_without_numbers()
			
			if category_numbers is not None:
				category_list.extend( category_numbers.get_category_list() )
				category_list.sort( key = lambda c: c.sequence )
				
			categories_field.choices = [(category.id, category.full_name()) for category in category_list]
			categories_field.label = _('Available Categories')
			self.helper['categories'].wrap( Field, size=12 )
			self.helper['competition'].wrap( Field, type='hidden' )
			
			for r in range(1, RANKING_MAX+1):
				self.helper[f'ranking_{r}_option'].wrap( Field, type='hidden' )
				self.helper[f'ranking_{r}'].wrap( Field, type='hidden' )
			
			for s in range(1, SORT_MAX+1):
				self.helper[f'sort_{s}'].wrap( Field, type='hidden' )
				
			addFormButtons( self, button_mask=button_mask )

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

#-----------------------------------------------------------------------

class CategoryNumbersRankSortAssignForm( Form ):
	@staticmethod
	def bib_field( participant ):
		return f'bib_{participant.id}'
		
	@staticmethod
	def get_initial( category_numbers ):
		initial = {}
		for r in range(1, RANKING_MAX+1):
			f = f'ranking_{r}_option'
			initial[f] = getattr( category_numbers, f )
			f = f'ranking_{r}'
			ranking = getattr( category_numbers, f )
			initial[f] = ranking.id if ranking else 0
			
		for s in range(1, SORT_MAX+1):
			f = f'sort_{s}'
			initial[f] = getattr( category_numbers, f )

		for p in category_numbers.get_participants().order_by():
			initial[CategoryNumbersRankSortAssignForm.bib_field(p)] = p.bib
		
		return initial
	
	def __init__( self, *args, **kwargs ):
		self.category_numbers = kwargs.pop( 'category_numbers' )
		super().__init__( *args, **kwargs )
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		ranking_choices = [(0,'---')] + [(r.id, r.name) for r in self.category_numbers.competition.ranking_set.all()]
		
		self.rank_fields = []
		for r in range(1, RANKING_MAX+1):
			f = f'ranking_{r}_option'
			self.fields[f] = forms.ChoiceField( choices=RANKING_OPTION, initial=1, required=False, label=f'ranking_{r}_option' )
			self.rank_fields.append( self[f] )
			f = f'ranking_{r}'
			self.fields[f] = forms.ChoiceField( choices=ranking_choices, required=False, label=f'ranking_{r}' )
			self.rank_fields.append( self[f] )
			
		self.sort_fields = []
		for s in range(1, SORT_MAX+1):
			f = f'sort_{s}'
			self.fields[f] = forms.ChoiceField( choices=self.category_numbers.SORT_CHOICES, label=f'sort_{s}' )
			self.sort_fields.append( self[f] )

		self.rows = []
		for p in self.category_numbers.get_participants_sorted():
			f = self.bib_field(p)
			self.fields[f] = forms.IntegerField( min_value=1, max_value=99999, required=False, initial=p.bib, widget=forms.NumberInput(attrs={'style': 'text-align: right; width: 8ch;'}) )
			self.rows.append( (self[f], p) )

	def save( self ):
		for r in range(1, RANKING_MAX+1):
			f = f'ranking_{r}_option'
			setattr( self.category_numbers, f, int(self.cleaned_data[f]) )
			f = f'ranking_{r}'
			setattr( self.category_numbers, f, Ranking.objects.filter( id=self.cleaned_data[f] ).first() )
			
		for s in range(1, SORT_MAX+1):
			f = f'sort_{s}'
			setattr( self.category_numbers, f, int(self.cleaned_data[f]) )
			
		self.category_numbers.save()

		numbers = self.category_numbers.get_numbers()
		
		bib_seen = set()
		to_update = []
		for p in self.category_numbers.get_participants_sorted():
			try:
				bib = int( self.cleaned_data[self.bib_field(p)] )
				if bib not in self.category_numbers or bib in bib_seen:
					bib = None			
			except (KeyError, TypeError, ValueError):
				bib = None
			
			if bib:
				bib_seen.add( bib )
			
			if p.bib != bib:
				p.bib = bib
				to_update.append( p )
		
		Participant.objects.bulk_update( to_update, ['bib'] )
		return bool( to_update )
	
@access_validation()
def CategoryNumbersAssign( request, categoryNumbersId ):
	category_numbers = get_object_or_404( CategoryNumbers, pk=categoryNumbersId )
	competition = category_numbers.competition
	
	if request.method == 'POST':
		form = CategoryNumbersRankSortAssignForm( request.POST, category_numbers=category_numbers )
		if form.is_valid():
			form.save()
			
	category_numbers = get_object_or_404( CategoryNumbers, pk=categoryNumbersId )
	form = CategoryNumbersRankSortAssignForm( initial=CategoryNumbersRankSortAssignForm.get_initial(category_numbers), category_numbers=category_numbers )
	
	return render( request, 'category_numbers_assign.html', locals() )
