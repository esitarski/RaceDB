from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from WriteLog import writeLog

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

def teams_from_search_text( search_text ):
	search_text = utils.normalizeSearch(search_text)
	q = Q()
	for n in search_text.split():
		q &= Q( search_text__contains = n )
	return Team.objects.filter(q)[:MaxReturn]

@access_validation()
def TeamsDisplay( request ):
	search_text = request.session.get('teams_filter', '')
	btns = [
		('new-submit', _('New Team'), 'btn btn-success'),
		('manage-duplicates-submit', _('Manage Duplicates'), 'btn btn-success'),
	]

	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'TeamNew') )
			
		if 'manage-duplicates-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'TeamManageDuplicates') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['teams_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
		
	teams = teams_from_search_text( search_text )
	return render( request, 'team_list.html', locals() )

@access_validation()
def TeamNew( request ):
	return GenericNew( Team, request, GetTeamForm(request) )
	
@access_validation()
def TeamEdit( request, teamId ):
	return GenericEdit( Team, request, teamId, GetTeamForm(request), template = 'team_form.html' )
	
@access_validation()
def TeamDelete( request, teamId ):
	return GenericDelete( Team, request, teamId, GetTeamForm(request), template = 'team_form.html' )
#-----------------------------------------------------------------------
class TeamManageDuplicatesSelectForm( Form ):
	selected		= forms.BooleanField( required=False, label='' )
	id				= forms.IntegerField( widget=forms.HiddenInput() )
	
	def __init__( self, *args, **kwargs ):
		initial = kwargs.get('initial', {})
		self.team_fields = {}
		for k in list(initial.iterkeys()):
			if k not in ('id', 'selected'):
				self.team_fields[k] = initial.pop(k)
		super(TeamManageDuplicatesSelectForm, self).__init__( *args, **kwargs )

	output_hdrs   = (_('Name'), _('Code'),      _('Type'),  _('Active'), _('# Members'))
	output_fields = (  'name', 'team_code',    'team_type',  'active', 'license_holder_count')
	output_bool_fields = set(['active',])
	output_center_fields = set(['license_holder_count'])
	
	def as_table( self ):
		s = StringIO()
		for f in self.output_fields:
			if f in self.output_bool_fields:
				v = int(self.team_fields.get(f,False))
				s.write( u'<td class="text-center"><span class="{}"></span></td>'.format(['is-err', 'is-good'][v]) )
			elif f in self.output_center_fields:
				s.write( u'<td class="text-center">{}</td>'.format(escape(unicode(self.team_fields.get(f,u'')))) )
			else:
				s.write( u'<td>{}</td>'.format(escape(unicode(self.team_fields.get(f,u'')))) )
		p = super(TeamManageDuplicatesSelectForm, self).as_table().replace( '<th></th>', '' ).replace( '<td>', '<td class="text-center">', 1 )
		ln = len('</tr>')
		return mark_safe( (p[:-ln] + s.getvalue() + p[-ln:]).replace('<tr>','').replace('</tr>','') )
		
TeamManageDuplicatesSelectFormSet = formset_factory(TeamManageDuplicatesSelectForm, extra=0, max_num=100000)

@access_validation()
def TeamManageDuplicates( request ):
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form_set = TeamManageDuplicatesSelectFormSet( request.POST )
		if form_set.is_valid():
			ids = [ d['id'] for d in form_set.cleaned_data if d['selected'] ]
			if len(ids) < 2:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
				
			request.session['team_manage_duplicate_ids'] = ids
			return HttpResponseRedirect(getContext(request,'cancelUrl') + 'TeamManageDuplicatesSelect/' )
	else:
		search_text = request.session.get('teams_filter', '')
		teams = teams_from_search_text( search_text )
		teams_initial = [
			{
				'id'		: t.id,
				'selected'	: False,
				'name'  	: t.name,
				'team_code'	: t.team_code,
				'team_type'	: t.get_team_type_display(),
				'license_holder_count': t.license_holder_count,
				'active'	: t.active,
			} for t in teams
		]
		form_set = TeamManageDuplicatesSelectFormSet( initial = teams_initial )			
	
	title = _('Select Duplicates, press Enter to proceed')
	if search_text:
		title = string_concat( title, u' (', _('search'), u'="', search_text, u'")' )
	headers = [_('Select')] + list(TeamManageDuplicatesSelectForm.output_hdrs)
	return render( request, 'team_manage_duplicates.html', locals() )

def get_team_cannonical_select_form( ids ):
	choices = []
	for i in ids:
		team = Team.objects.filter( id=i ).first()
		if not team:
			continue
		fields = [team.name]
		if team.team_code:
			fields.extend( [u', (', team.team_code, u')'] )
		fields.extend( [u', ', team.get_team_type_display()] )
		if team.nation_code:
			fields.extend( [u', ', team.nation_code] )
		fields.extend( [u', ', [_('Inactive'), _('Active')][int(team.active)]] )
		choices.append( (i, string_concat(*fields) ) )
	
	class TeamCannonicalSelectForm( Form ):
		cannonical = forms.ChoiceField( choices=choices, required=True, label=_('Select Representative Team') )
		
		def __init__( self, *args, **kwargs ):
			super( TeamCannonicalSelectForm, self ).__init__( *args, **kwargs )
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'select-cannonical-submit', _('Merge Teams with Representative Team'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			self.helper.layout = Layout(
				Row(
					Field('cannonical', size=len(choices)),
				),
				Row( *button_args ),
			)
			
	return TeamCannonicalSelectForm		

def team_merge_duplicates( ids, cannonical ):
	team_cannonical = Team.objects.filter( id=cannonical ).first()
	if not team_cannonical:
		return
	duplicate_ids = [i for i in ids if i != cannonical]
	if not duplicate_ids:
		return
	teams = Team.objects.filter(id__in=duplicate_ids)
	
	# Record the merge in the log.
	def get_team_info( t ):
		return u'"{}" code="{}" type="{}" nation="{}" active={}\n'.format(
			t.name,
			t.team_code,
			t.get_team_type_display(),
			t.nation_code,
			t.active,
		)
	
	description = StringIO()
	for t in teams:
		description.write( get_team_info(t) )
	description.write( u'--->\n' )
	t = team_cannonical
	description.write( get_team_info(t) )
	UpdateLog( update_type=1, description=description.getvalue() ).save()
	description.close()
	
	for cls in [Participant, TeamHint]:
		cls.objects.filter(team__in=teams).update(team=team_cannonical)
	Team.objects.filter( id__in=duplicate_ids ).delete()

@access_validation()
def TeamManageDuplicatesSelect( request ):
	ids = request.session.get('team_manage_duplicate_ids', [])
	if not ids:
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			request.session['team_manage_duplicate_ids'] = []
			return HttpResponseRedirect(getContext(request,'cancelUrl'))

		form = get_team_cannonical_select_form(ids)( request.POST )
		if form.is_valid():
			cannonical = int( form.cleaned_data['cannonical'] )
			request.session['team_manage_duplicate_cannonical'] = cannonical
			team_merge_duplicates( ids, cannonical )
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = get_team_cannonical_select_form(ids)()
	
	title = _('Select the Representative Team to merge the Duplicate to')
	return render( request, 'generic_form.html', locals() )


