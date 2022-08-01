from django.utils.translation import gettext_lazy as _
from django.utils.html import escape

from .views_common import *
from .WriteLog import writeLog

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
			
			super().__init__(*args, **kwargs)
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
					Col(Field('contact', size=40), 4),
					Col(Field('contact_email', size=30), 4),
					Col(Field('contact_phone', size=22), 4),
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
		q &= Q( search_text__icontains = n )
	return Team.objects.filter(q)[:MaxReturn]

@access_validation()
def TeamsDisplay( request ):
	search_text = request.session.get('teams_filter', '')
	btns = [
		('new-submit', _('New Team'), 'btn btn-success'),
		('manage-duplicates-submit', _('Manage Duplicates'), 'btn btn-success'),
	]

	if request.method == 'POST':
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
	#alias_conflicts = TeamAlias.alias_conflicts()
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
		for k in list(initial.keys()):
			if k not in ('id', 'selected'):
				self.team_fields[k] = initial.pop(k)
		self.team_id = initial.get('id', None)
		super().__init__( *args, **kwargs )

	output_hdrs   = (_('Name'), _('Code'),      _('Type'),  _('Active'), _('# Members'))
	output_fields = (  'name', 'team_code',    'team_type',  'active', 'license_holder_count')
	output_bool_fields = set(['active',])
	output_center_fields = set(['license_holder_count'])
	
	def as_table( self ):
		s = StringIO()
		for f in self.output_fields:
			if f in self.output_bool_fields:
				v = int(self.team_fields.get(f,False))
				s.write( '<td class="text-center"><span class="{}"></span></td>'.format(['is-err', 'is-good'][v]) )
			elif f in self.output_center_fields:
				s.write( '<td class="text-center">{}</td>'.format(escape('{}'.format(self.team_fields.get(f,'')))) )
			elif f == 'name':
				team = Team.objects.get(id=self.team_id)
				s.write( '<td>{}<br/>{}</td>'.format(team.name, team.get_team_aliases_html()) )
			else:
				s.write( '<td>{}</td>'.format(escape('{}'.format(self.team_fields.get(f,'')))) )
		p = super().as_table().replace( '<th></th>', '' ).replace( '<td>', '<td class="text-center">', 1 )
		ln = len('</tr>')
		return mark_safe( (p[:-ln] + s.getvalue() + p[-ln:]).replace('<tr>','').replace('</tr>','') )
		
TeamManageDuplicatesSelectFormSet = formset_factory(TeamManageDuplicatesSelectForm, extra=0, max_num=100000)

@access_validation()
def TeamManageDuplicates( request ):
	if request.method == 'POST':
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
		title = format_lazy( '{} ({}={})', title,  _('search'), search_text )
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
			fields.extend( [', (', team.team_code, ')'] )
		fields.extend( [', ', team.get_team_type_display()] )
		if team.nation_code:
			fields.extend( [', ', team.nation_code] )
		fields.extend( [', ', [_('Inactive'), _('Active')][int(team.active)]] )
		choices.append( (i, format_lazy('{}'*len(fields), *fields) ) )
	
	class TeamCannonicalSelectForm( Form ):
		cannonical = forms.ChoiceField(
			choices=choices, required=True,
			label=_('Select Representative Team'),
			widget=forms.RadioSelect,
		)
		
		def __init__( self, *args, **kwargs ):
			super().__init__( *args, **kwargs )
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = ''
			
			button_args = [
				Submit( 'select-cannonical-submit', _('Merge Teams with Representative Team'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),	# Keep this as a Submit button.
			]
			self.helper.layout = Layout(
				Row(
					HTML('<div class="well">'), Field('cannonical'), HTML('</div>'),
				),
				Row( *button_args ),
				Row( HTML(_('Note: Merged Team Names will also be added to the Team Alias list.')) ),
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
		return '"{}" code="{}" type="{}" nation="{}" active={}\n'.format(
			t.name,
			t.team_code,
			t.get_team_type_display(),
			t.nation_code,
			t.active,
		)
	
	description = StringIO()
	for t in teams:
		description.write( get_team_info(t) )
		
		# Add the duplicate team name to the cannonical team's aliases.
		if not TeamAlias.objects.filter( team=team_cannonical, alias=t.name ).exists():
			TeamAlias( team=team_cannonical, alias=t.name ).save()
			
	# Add any duplicate team aliases from the old team to the cannonical team.
	# Otherwise old aliases will be deleted in the cascade delete.
	for ta in list(TeamAlias.objects.filter(team__id__in=duplicate_ids)):
		if not TeamAlias.objects.filter( team=team_cannonical, alias=ta.alias ).exists():
			ta.team = team_cannonical
			ta.save()
	
	description.write( '--->\n' )
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

#--------------------------------------------------------------------------------
@access_validation()
def TeamAliasNew( request, teamId ):
	team = get_object_or_404( Team, pk=teamId )
	TeamAlias( team=team, alias = '{} - Alias'.format(team.name) ).save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@autostrip
class TeamAliasForm( ModelForm ):
	class Meta:
		model = TeamAlias
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('alias', size=100), 12),
			),
			Row(
				Field( 'team', type='hidden' ),
			)
		)
		addFormButtons( self, button_mask )

@access_validation()
def TeamAliasEdit( request, teamAliasId ):
	return GenericEdit( TeamAlias, request, teamAliasId, TeamAliasForm, template = 'team_alias_form.html' )
	
@access_validation()
def TeamAliasDelete( request, teamAliasId ):
	return GenericDelete( TeamAlias, request, teamAliasId, TeamAliasForm, template = 'team_alias_form.html' )

