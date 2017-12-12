from views_common import *
from django.forms import modelformset_factory
import xlsxwriter
from xlrd import open_workbook
from FieldMap import standard_field_map
from import_utils import *

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

def ccos_to_excel( competition ):
	CompetitionCategoryOption.normalize( competition )
	ccos_query = competition.competitioncategoryoption_set.all().order_by('category__sequence').select_related('category')
		
	output = StringIO()
	wb = xlsxwriter.Workbook( output, {'in_memory': True} )
	title_format = wb.add_format( dict(bold=True) )
	
	sheet_name = 'RaceDB-CCO'
	ws = wb.add_worksheet(sheet_name)
	
	row = 0
	
	ws.write( row, 0, unicode(_('Category')), title_format )
	ws.write( row, 1, unicode(_('Check License')), title_format )
	ws.write( row, 2, unicode(_('Note')), title_format )
	
	for cco in ccos_query:
		row += 1
		ws.write( row, 0, cco.category.code_gender )
		ws.write( row, 1, cco.check_license )
		ws.write( row, 2, cco.note )
			
	wb.close()
	return sheet_name, output.getvalue()

def ccos_from_excel( competition, worksheet_contents, sheet_name=None ):
	CompetitionCategoryOption.normalize( competition )
	ccos_query = competition.competitioncategoryoption_set.all().order_by('category__sequence').select_related('category')

	wb = open_workbook( file_contents = worksheet_contents )
	
	ur_records = []
	import_utils.datemode = wb.datemode
	
	ws = None
	for cur_sheet_name in wb.sheet_names():
		if cur_sheet_name == sheet_name or sheet_name is None:
			ws = wb.sheet_by_name(cur_sheet_name)
			break
	
	if not ws:
		return
	
	ccos = {cco.query.code_gender.lower():cco for cco in ccos_query}
	
	ifm = standard_field_map()

	num_rows = ws.nrows
	for r in xrange(num_rows):
		row = ws.row( r )
		if r == 0:
			# Get the header fields from the first row.
			fields = [unicode(v.value).strip() for v in row]
			ifm.set_headers( fields )
			continue
		
		v = ifm.finder( row )
		code_gender = v('category_code', None)
		if not code_gender:
			continue
		try:
			cco = ccos[code_gender.strip().lower()]
		except KeyError:
			continue
		
		check_license = to_bool(v('check_license', None))		
		if check_license is not None:
			cco.check_license = check_license
		
		note = v('note', None)
		if note is not None:
			cco.note = unicode(note)
		
		cco.save()
		
