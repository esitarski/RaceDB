from django.utils.translation import gettext_lazy as _

from .views_common import *
from .init_ranking import init_ranking
from .FieldMap import standard_field_map

@autostrip
class UploadRankingForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx)') )
	
	def __init__( self, *args, **kwargs ):
		super().__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xlsx"), 8),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_ranking( rankingId, excel_contents ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO()
	init_ranking(
		rankingId=rankingId,
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
	)
	results_str = message_stream.getvalue()
	return results_str

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def UploadRanking( request, rankingId ):
	ranking = get_object_or_404( Ranking, pk=rankingId )
	competition = ranking.competition
	
	if request.method == 'POST':
		form = UploadRankingForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_ranking( rankingId, request.FILES['excel_file'] )
	else:
		form = UploadRankingForm()
	
	ranking_entries = list( ranking.rankingentry_set.all().order_by('rank').iterator() )
	all_uci_ids = all( re.uci_id for re in ranking_entries )
	all_license_codes = all( re.license_code for re in ranking_entries )
	if not all_uci_ids and all_license_codes:
		match_key = 1
	else:
		match_key = 0
	if match_key != ranking.match_key:
		ranking_match_key = match_key
		ranking.save()

	ifm = standard_field_map()
	column_info = [(f, ifm.get_aliases(f), optional, ifm.get_description(f)) for f, optional in (('uci_id', True), ('license_code', True), ('rank', False), ('points', True))]

	return render( request, 'upload_ranking.html', locals() )

@autostrip
class RankingForm( ModelForm ):
	class Meta:
		model = Ranking
		fields = '__all__'
		
	def importFromExcelCB( self, request, ranking ):
		return HttpResponseRedirect( pushUrl(request,'RankingImportFromExcel', ranking.id) )
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super().__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		
		self.helper.layout = Layout(
			Row(
				Field('name', size=32),
				Field('description', size=80),
			),
			Row(
				Field('match_key'),
			),
			Field( 'competition', type='hidden' ),
		)
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
					( 'mport-from_excel-submit', _('Import from Excel'), 'btn btn-primary', self.importFromExcelCB ),
			])
			
		addFormButtons( self, button_mask, self.additional_buttons )
		
@access_validation()
def RankingsDisplay( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	rankings = competition.ranking_set.all()
	return render( request, 'rankings_list.html', locals() )

@access_validation()
def RankingNew( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return GenericNew( Ranking, request, RankingForm, instance_fields={'competition':competition} )

@access_validation()
def RankingEdit( request, rankingId ):
	ranking = get_object_or_404( Ranking, pk=rankingId )
	return GenericEdit( Ranking, request, rankingId, RankingForm )
	
@access_validation()
def RankingDelete( request, rankingId ):
	return GenericDelete( Ranking, request, rankingId, RankingForm )

@access_validation()
def RankingImportFromExcel( request, rankingId ):
	return UploadRanking( request, rankingId )
#--------------------------------------------------------------------------------------------
