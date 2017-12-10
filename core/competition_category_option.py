from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.forms import formset_factory

class LicenseCheckForm( forms.Form ):
	license_check_required = forms.BooleanField( required=False )
	category_id = forms.CharField( widget=forms.HiddenInput() )

LicenseCheckFormSet = formset_factory( LicenseCheckForm, extra=0 )
	
def SetLicenseChecks( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	CompetitionCategoryOption.normalize( competition )
	
	ccos_query = competition.competitioncategoryoption_set.all().order_by('category__sequence').select_related('category')
	ccos = list(ccos_query)
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect( getContext(request, 'cancelUrl') )
			
		if 'set-all-submit' in request.POST:
			ccos_query.update( license_check_required=True )
			return HttpResponseRedirect( '.' )
			
		if 'clear-all-submit' in request.POST:
			ccos_query.update( license_check_required=False )
			return HttpResponseRedirect( '.' )
			
		form_set = LicenseCheckFormSet( request.POST )
		if form_set.is_valid():
			for f in form_set:
				fields = f.cleaned_data
				category = get_object_or_404( Category, pk=fields['category_id'] )
				CompetitionCategoryOption.set_license_check_required( competition, category, fields['license_check_required'] )
			return HttpResponseRedirect( getContext(request, 'cancelUrl') )
	else:
		initial = [
			{	'license_check_required':cco.license_check_required,
				'category_id':unicode(cco.category.id),
			} for cco in ccos
		]
		form_set = LicenseCheckFormSet( initial=initial )

	category_forms = [(cco.category, f) for cco, f in zip(ccos, form_set)]
	return render( request, 'cco_license_check_form.html', locals() )
