from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.forms import formset_factory
from django.db import transaction

class LicenseCheckForm( forms.Form ):
	license_check_required = forms.BooleanField( required=False )
	note = forms.CharField( blank=True )
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
			to_set, to_clear, to_note = [], [], []
			for f in form_set:
				fields = f.cleaned_data
				(to_set if fields['license_check_required'] else to_clear).append( fields['category_id'] )
				to_note.append( (fields['category_id'], fields['note']) )
			CompetitionCategoryOption.objects.filter( competition=competition, category__in=to_set ).update( license_check_required=True )
			CompetitionCategoryOption.objects.filter( competition=competition, category__in=to_clear ).update( license_check_required=False )
			with transaction.atomic():
				for category_id, note in to_note:
					coo = CompetitionCategoryOption.objects.get( competition=competition, category__id=category_id )
					coo.note = note
					coo.save()
			return HttpResponseRedirect( getContext(request, 'cancelUrl') )
	else:
		initial = [
			{
				'license_check_required':cco.license_check_required,
				'note':cco.note,
				'category_id':unicode(cco.category.id),
			} for cco in ccos
		]
		form_set = LicenseCheckFormSet( initial=initial )

	category_forms = [(cco.category, f) for cco, f in zip(ccos, form_set)]
	return render( request, 'cco_license_check_form.html', locals() )
