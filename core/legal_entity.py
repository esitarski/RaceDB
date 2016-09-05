from views_common import *
from django.utils.translation import ugettext_lazy as _

@autostrip
class LegalEntityForm( ModelForm ):
	class Meta:
		model = LegalEntity
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super(LegalEntityForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('name', size=40), 4),
			),
			Row(
				Col(Field('contact', size=40), 4),
				Col(Field('email', size=40), 4),
				Col(Field('phone', size=40), 4),
			),
			Row(
				Col(Field('website', size=60),12),
			),
			Row(
				Field('waiver_expiry_date'),
				HTML('<strong><span style="font-size: 130%">'),
				HTML(_('All waivers signed <span style="text-decoration: underline;">before</span> this date will be flagged as expired.')),
				HTML('</span></strong>'),
			),
			Row( HTML('<hr/>') ),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
def LegalEntitiesDisplay( request ):
	search_text = request.session.get('legal_entities_filter', '')
	btns = [('new-submit', _('New LegalEntity'), 'btn btn-success')]
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LegalEntityNew') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['legal_entities_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
		
	search_text = utils.normalizeSearch(search_text)
	q = Q()
	for n in search_text.split():
		q &= Q( name__icontains = n )
	legal_entities = LegalEntity.objects.filter(q)[:MaxReturn]
	return render( request, 'legal_entity_list.html', locals() )
	
@access_validation()
def LegalEntityNew( request ):
	return GenericNew( LegalEntity, request, LegalEntityForm )
	
@access_validation()
def LegalEntityEdit( request, legalEntityId ):
	return GenericEdit( LegalEntity, request, legalEntityId, LegalEntityForm )
	
@access_validation()
def LegalEntityDelete( request, legalEntityId ):
	return GenericDelete( LegalEntity, request, legalEntityId, LegalEntityForm )

