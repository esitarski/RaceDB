from views_common import *
from django.forms import modelformset_factory

CompetitionCategoryOptionFormSet = modelformset_factory(
	CompetitionCategoryOption, fields='__all__',
	widgets={
		'note': forms.TextInput(attrs={'size':40}),
		'competition': forms.HiddenInput(),
		'category': forms.HiddenInput(),
	},
	extra=0,
)
	
def SetLicenseChecks( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	CompetitionCategoryOption.normalize( competition )
	
	ccos_query = competition.competitioncategoryoption_set.all().order_by('category__sequence').select_related('category')
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect( getContext(request, 'cancelUrl') )
			
		if 'set-all-submit' in request.POST:
			ccos_query.update( license_check_required=True )
			return HttpResponseRedirect( '.' )
			
		if 'clear-all-submit' in request.POST:
			ccos_query.update( license_check_required=False )
			return HttpResponseRedirect( '.' )
			
		form_set = CompetitionCategoryOptionFormSet( request.POST, prefix='cco' )
		if form_set.is_valid():
			form_set.save()
			return HttpResponseRedirect( getContext(request, 'cancelUrl') )
	else:
		form_set = CompetitionCategoryOptionFormSet( queryset=ccos_query, prefix='cco' )

	return render( request, 'cco_license_check_form.html', locals() )
