from views_common import *
from django.utils.translation import ugettext_lazy as _

def GetTeamForm( request ):
	is_superuser = request.user.is_superuser
	
	@autostrip
	class TeamForm( ModelForm ):
		class Meta:
			model = Team
			if not is_superuser:
				widgets = {'active': forms.HiddenInput()}
			else:
				widgets = {}
			fields = '__all__'
			
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			
			super(TeamForm, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.helper.layout = Layout(
				Row(
					Col(Field('name', size=100), 12),
				),
				Row(
					Col(Field('team_code', size=12), 2),
					Col('team_type', 2),
					Col('nation_code', 3),
					Col('active', 2),
				),
				Row(
					HTML('&nbsp'*8),
				)
			)
			addFormButtons( self, button_mask )
	
	return TeamForm

@access_validation()
def TeamsDisplay( request ):
	search_text = request.session.get('teams_filter', '')
	btns = [('new-submit', _('New Team'), 'btn btn-success')]
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'TeamNew') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['teams_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
		
	search_text = utils.normalizeSearch(search_text)
	q = Q()
	for n in search_text.split():
		q &= Q( search_text__contains = n )
	teams = Team.objects.filter(q)[:MaxReturn]
	return render( request, 'team_list.html', locals() )

@access_validation()
def TeamNew( request ):
	return GenericNew( Team, request, GetTeamForm(request) )
	
@access_validation()
def TeamEdit( request, teamId ):
	return GenericEdit( Team, request, teamId, GetTeamForm(request) )
	
@access_validation()
def TeamDelete( request, teamId ):
	return GenericDelete( Team, request, teamId, GetTeamForm(request) )

