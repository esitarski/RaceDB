from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib.auth.views import logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt

from subprocess import Popen, PIPE
import uuid
import zipfile
import operator
import itertools

from get_crossmgr_excel import get_crossmgr_excel, get_crossmgr_excel_tt
from get_seasons_pass_excel import get_seasons_pass_excel
from get_number_set_excel import get_number_set_excel
from get_start_list_excel import get_start_list_excel
from get_license_holder_excel import get_license_holder_excel
from get_participant_excel import get_participant_excel
from participation_excel import participation_excel
from participation_data import participation_data, get_competitions
from year_on_year_data import year_on_year_data
from license_holder_import_excel import license_holder_import_excel

from participant_key_filter import participant_key_filter, participant_bib_filter
from init_prereg import init_prereg
from emails import show_emails

from print_bib import print_bib_tag_label, print_id_label, print_body_bib, print_shoulder_bib
from gs_cmd import gs_cmd

import read_results

from ReadWriteTag import ReadTag, WriteTag
from FinishLynx import FinishLynxExport
from AnalyzeLog import AnalyzeLog
import WriteLog

#-----------------------------------------------------------------------
from context_processors import getContext

from django.views.decorators.cache import patch_cache_control

@access_validation()
def home( request, rfid_antenna=None ):
	if rfid_antenna is not None:
		try:
			request.session['rfid_antenna'] = int(rfid_antenna)
		except Exception as e:
			pass
	version = RaceDBVersion
	return render( request, 'home.html', locals() )
	
#-----------------------------------------------------------------------

@autostrip
class LicenseHolderTagForm( Form ):
	tag = forms.CharField( required = False, label = _('Tag') )
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label = _('RFID Antenna to Write Tag') )
	
	def __init__(self, *args, **kwargs):
		super(LicenseHolderTagForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Update Tag in Database'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			Submit( 'auto-generate-tag-submit', _('Auto Generate Tag Only - Do Not Write'), css_class = 'btn btn-primary' ),
			Submit( 'write-tag-submit', _('Write Existing Tag'), css_class = 'btn btn-primary' ),
			Submit( 'read-validate-tag-submit', _('Read / Validate Tag'), css_class = 'btn btn-primary' ),
			Submit( 'auto-generate-and-write-tag-submit', _('Auto Generate and Write Tag'), css_class='btn btn-success' ),
		]
		
		self.helper.layout = Layout(
			Row(
				Col( Field('tag', cols = '60'), 4 ),
				Col( HTML('&nbsp;' * 20 ),4 ),
				Col( Field('rfid_antenna'), 4 ),
			),
			HTML( '<br/>' ),
			Row(
				button_args[5],
				HTML( '&nbsp;' * 5 ),
				button_args[3],
				HTML( '&nbsp;' * 5 ),
				button_args[4],
			),
			HTML( '<br/>' * 2 ),
			Row(
				button_args[2],
			),
			HTML( '<br/>' * 2 ),
			Row( 
				button_args[0],
				HTML( '&nbsp;' * 5 ),
				button_args[1],
			),
		)

@access_validation()
def LicenseHolderTagChange( request, licenseHolderId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = LicenseHolderTagForm( request.POST )
		if form.is_valid():
			status = True
			status_entries = []

			tag = form.cleaned_data['tag'].strip().upper()
			rfid_antenna = request.session['rfid_antenna'] = int(form.cleaned_data['rfid_antenna'])
			
			if 'auto-generate-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				tag = license_holder.get_unique_tag()
			
			license_holder.existing_tag = tag
			try:
				license_holder.save()
			except Exception as e:
				# Report the error - probably a non-unique field.
				status = False
				status_entries.append(
					(_('LicenseHolder') + u': ' + _('Existing Tag Save Exception:'), (
						unicode(e),
					)),
				)
				return render( request, 'rfid_write_status.html', locals() )
			
			# Check for tag actions.
			if any(submit_btn in request.POST for submit_btn in ('read-validate-tag-submit','write-tag-submit','auto-generate-and-write-tag-submit') ):
			
				# Check for valid antenna.
				if not rfid_antenna:
					status = False
					status_entries.append(
						(_('RFID Antenna Configuration'), (
							_('RFID Antenna for Tag Write must be specified.'),
							_('Please specify the RFID Antenna.'),
						)),
					)
				
				# Check for missing tag.
				if not tag:
					status = False
					status_entries.append(
						(_('Empty Tag'), (
							_('Cannot write/validate an empty Tag.'),
							_('Please specify a Tag or press Cancel.'),
						)),
					)
				
				# Check for valid tag.
				elif not utils.allHex(tag):
					status = False
					status_entries.append(
						(_('Non-Hex Characters in Tag'), (
							_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
							_('Please change the Tag to all hexadecimal.'),
						)),
					)
				
				if status:
					if 'read-validate-tag-submit' in request.POST:
						# Handle reading/validating an existing tag.
						status, response = ReadTag(rfid_antenna)
						tagRead = ''
						# DEBUG DEBUG
						#status, response = True, {'tags': ['E26D00061114']}
						if not status:
							status_entries.append(
								(_('Tag Read Failure'), response.get('errors',[]) ),
							)
						else:
							tags = response.get('tags', [])
							try:
								tagRead = tags[0]
							except (AttributeError, IndexError) as e:
								status = False
								status_entries.append(
									(_('Tag Read Failure'), [e] ),
								)
						
						if tagRead and len(tags) > 1:
							status = False
							status_entries.append(
								(_('Multiple Tags Read'), tags ),
							)
						elif status:
							if tagRead != tag:
								try:
									license_holder_other = LicenseHolder.objects.get(existing_tag=tagRead)
									additional_message = u'{} != {} ({})'.format(tag, tagRead, license_holder_other.full_name())
								except  (LicenseHolder.DoesNotExist, LicenseHolder.MultipleObjectsReturned) as e:
									additional_message = u'{} != {}'.format(tag, tagRead)
								status = False
								status_entries.append(
									(_('Tag read does NOT match rider tag'), [additional_message] ),
								)
							else:
								status_entries.append(
									(_('Tag read matches rider tag'), [u'{} = {}'.format(tag, tagRead)] ),
								)
						return render( request, 'rfid_validate.html', locals() )
					else:
						# Handle writing the tag.
						status, response = WriteTag(tag, rfid_antenna)
						if not status:
							status_entries = [
								(_('Tag Write Failure'), response.get('errors',[]) ),
							]
				
				if not status:
					return render( request, 'rfid_write_status.html', locals() )
				# if status: fall through to ok-submit case.
			
			# ok-submit
			if 'auto-generate-tag-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'path'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = LicenseHolderTagForm( initial = dict(tag=license_holder.existing_tag, rfid_antenna=rfid_antenna) )
		
	return render( request, 'license_holder_tag_change.html', locals() )

#--------------------------------------------------------------------------------------------

@autostrip
class LicenseHolderForm( ModelForm ):
	class Meta:
		model = LicenseHolder
		fields = '__all__'
		
	def manageTag( self, request, license_holder ):
		return HttpResponseRedirect( pushUrl(request, 'LicenseHolderTagChange', license_holder.id) )
	
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		lh = kwargs.get( 'instance', None )
	
		super(LicenseHolderForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		def error_html( error ):
			return u'<span class="help-block"><strong>{}{}</strong>'.format(u'&nbsp;'*8,error) if error else u''
		
		def warning_html( warning ):
			return '<img src="{}" style="width:20px;height:20px;"/>'.format(static('images/warning.png')) if warning else ''
		
		def uci_code_html():
			if lh and lh.uci_country:
				return u'<h4><br/><img class="flag" src="{}"/>&nbsp;{}</h4>'.format(static('flags/{}.png'.format(lh.uci_country)), lh.uci_code)
			return ''
		
		def nation_code_html():
			if lh and lh.nation_code:
				return u'<h4><br/><img class="flag" src="{}"/>&nbsp;{}</h4>'.format(static('flags/{}.png'.format(lh.nation_code)), lh.nation_code)
			return ''
		
		self.helper.layout = Layout(
			#Field( 'id', type='hidden' ),
			Row(
				Col(Field('last_name', size=40), 4),
				Col(Field('first_name', size=40), 4),
				Col('gender', 2),
				ColKey(
					HTML(warning_html(lh and lh.date_of_birth_error)),
					Field('date_of_birth', size=10),
					HTML(error_html(lh and lh.date_of_birth_error)),
					cols=2),
			),
			Row(
				Col(Field('city', size=40), 3),
				Col(Field('state_prov', size=20), 3),
				Col(Field('nationality', size=20), 2),
				Col(Field('nation_code', size=3), 2),
				Col(Field('zip_postal', size=10), 2),
			),
			Row(
				Col(Field('email', size=50), 6),
				Col(Field('phone', size=20), 4),
				Col(HTML('<button id="idSendEmail class="btn btn-primary" onClick="sendEmail()">Send Email</button>'), 1),
			),
			Row(
				ColKey(
					HTML(warning_html(lh and lh.license_code_error)),
					Field('license_code'),
					HTML(error_html(lh and lh.license_code_error)),
					cols=3,
				),
				ColKey(
					HTML(warning_html(lh and lh.uci_id_error)),
					Field('uci_id'),
					HTML(error_html(lh and lh.uci_id_error)),
					cols=4,
				),
				ColKey(
					HTML(warning_html(lh and lh.uci_code_error)),
					Field('uci_code'),
					HTML(error_html(lh and lh.uci_code_error)),
					cols=3,
				),
				Col(HTML(nation_code_html()), 2),
			),
			Row(
				Col('existing_tag', 3),
				Col('existing_tag2', 3),
				Col('active', 3),
			),
			Row(
				ColKey(
					HTML(warning_html(lh and not lh.emergency_contact_name)),
					Field('emergency_contact_name', size=50),
					cols=6,
				),
				ColKey(
					HTML(warning_html(lh and not lh.emergency_contact_phone)),
					Field('emergency_contact_phone'),
					cols=4,
				),
			),
			Row(
				Col('eligible', 2),
				Col( HTML(_('If not Eligible to Compete, this License Holder will not be allowed to participate in races until it is reset.  Always add a note (below) explaining the reason.')), 6 ),
			),
			Row(
				Field('note', cols=80, rows=4),
			),
		)
		
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.append( ('manage-tag-submit', _('Manage Chip Tag'), 'btn btn-success', self.manageTag), )
		
		addFormButtons( self, button_mask, additional_buttons=self.additional_buttons )

reUCICode = re.compile( '^[A-Z]{3}[0-9]{8}$', re.IGNORECASE )
def is_uci_id( uci_id ):
	uci_id = uci_id.replace(' ','')
	return uci_id.isdigit() and not uci_id.startswith('0') and len(uci_id) == 11 and int(uci_id[:-2]) % 97 == int(uci_id[-2:])

def license_holders_from_search_text( search_text ):
	search_text = utils.normalizeSearch(search_text)
	license_holders = []
	while True:
		if search_text.startswith( 'rfid=' ):
			try:
				arg = search_text.split('=',1)[1].strip().upper().lstrip('0')
				license_holders = [LicenseHolder.objects.get(Q(existing_tag=arg) | Q(existing_tag2=arg))]
				break
			except (IndexError, LicenseHolder.DoesNotExist):
				break
			except LicenseHolder.MultipleObjectsReturned:
				pass
			
		if search_text.startswith( 'scan=' ):
			try:
				arg = search_text.split('=',1)[1].strip().upper().lstrip('0')
				license_holders = [LicenseHolder.objects.get(Q(license_code=arg) | Q(uci_id=arg) | Q(uci_code=arg) | Q(existing_tag=arg) | Q(existing_tag2=arg))]
				break
			except (IndexError, LicenseHolder.DoesNotExist):
				break
			except LicenseHolder.MultipleObjectsReturned:
				pass
	
		if reUCICode.match(search_text):
			try:
				license_holders = [LicenseHolder.objects.get(uci_code = search_text.upper())]
				break
			except (LicenseHolder.DoesNotExist, LicenseHolder.MultipleObjectsReturned) as e:
				pass
				
		if is_uci_id( search_text ):
			try:
				license_holders = [LicenseHolder.objects.get(uci_id = search_text.replace(' ',''))]
				break
			except (LicenseHolder.DoesNotExist, LicenseHolder.MultipleObjectsReturned) as e:
				pass
		
		if search_text[-4:].isdigit():
			try:
				license_holders = [LicenseHolder.objects.get(license_code = search_text.upper().lstrip('0'))]
				break
			except (LicenseHolder.DoesNotExist, LicenseHolder.MultipleObjectsReturned) as e:
				pass
		
		q = Q()
		for n in search_text.split():
			q &= Q( search_text__contains = n )
		license_holders = LicenseHolder.objects.filter(q)[:MaxReturn]
		break
	return license_holders
	
@access_validation()
def LicenseHoldersDisplay( request ):

	search_text = request.session.get('license_holder_filter', '')
	btns = [
		('search-by-barcode-submit', _('Barcode Search'), 'btn btn-primary', True),
		('search-by-tag-submit', _('RFID Search'), 'btn btn-primary', True),
		('clear-search-submit', _('Clear Search'), 'btn btn-primary', True),
		('new-submit', _('New LicenseHolder'), 'btn btn-success'),
		('correct-errors-submit', _('Correct Errors'), 'btn btn-primary'),
		('manage-duplicates-submit', _('Manage Duplicates'), 'btn btn-primary'),
		('auto-create-tags-submit', _('Auto Create All Tags'), 'btn btn-primary'),
		('export-excel-submit', _('Export to Excel'), 'btn btn-primary'),
		('import-excel-submit', _('Import from Excel'), 'btn btn-primary'),
	]
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'search-by-barcode-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderBarcodeScan') )
			
		if 'search-by-tag-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderRfidScan') )
			
		if 'clear-search-submit' in request.POST:
			request.session['license_holder_filter'] = ''
			return HttpResponseRedirect( '.' )
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderNew') )
			
		if 'correct-errors-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHoldersCorrectErrors') )
			
		if 'manage-duplicates-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHoldersManageDuplicates') )
			
		if 'auto-create-tags-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHoldersAutoCreateTags') )
			
		if 'import-excel-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHoldersImportExcel') )
			
		form = SearchForm( btns, request.POST )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['license_holder_filter'] = search_text
			
			if 'export-excel-submit' in request.POST:
				q = Q()
				for n in search_text.split():
					q &= Q( search_text__contains = n )
				xl = get_license_holder_excel( q )
				response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
				response['Content-Disposition'] = 'attachment; filename=RaceDB-LicenseHolders-{}.xlsx'.format(
					datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
				)
				return response
	else:
		form = SearchForm( btns, initial = {'search_text': search_text} )
	
	license_holders = license_holders_from_search_text( search_text )
	isEdit = True
	return render( request, 'license_holder_list.html', locals() )

#--------------------------------------------------------------------------
@autostrip
class BarcodeScanForm( Form ):
	scan = forms.CharField( required = False, label = _('Barcode (License Code or RFID Tag)') )
	
	def __init__(self, *args, **kwargs):
		hide_cancel_button = kwargs.pop('hide_cancel_button', None)
		super(BarcodeScanForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		if hide_cancel_button:
			button_args = button_args[:-1]
		
		self.helper.layout = Layout(
			Row(
				Field('scan', size=40),
			),
			Row( *button_args ),
		)

@access_validation()
def LicenseHolderBarcodeScan( request ):
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = BarcodeScanForm( request.POST )
		if form.is_valid():
			scan = form.cleaned_data['scan'].strip()
			if not scan:
				return HttpResponseRedirect(getContext(request,'path'))
				
			request.session['license_holder_filter'] = u'scan={}'.format(scan.lstrip('0'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = BarcodeScanForm()
		
	return render( request, 'license_holder_scan_form.html', locals() )

#--------------------------------------------------------------------------

@autostrip
class RfidScanForm( Form ):
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label=_('RFID Antenna to Read Tag') )
	
	def __init__(self, *args, **kwargs):
		hide_cancel_button = kwargs.pop( 'hide_cancel_button', None )
		super(RfidScanForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'read-tag-submit', _('Read Tag'), css_class = 'btn btn-primary  btn-lg', id='focus' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		if hide_cancel_button:
			button_args = button_args[:-1]
			
		self.helper.layout = Layout(
			Row( *button_args ),
			HTML('<br/>' * 12),
			Row(
				Col(Field('rfid_antenna'), 6 ),
			),
		)

#-----------------------------------------------------------------------
@access_validation()
def LicenseHolderRfidScan( request ):
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	status = True
	status_entries = []
	tag = None
	tags = []
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = RfidScanForm( request.POST )
		if form.is_valid():
		
			request.session['rfid_antenna'] = rfid_antenna = int(form.cleaned_data['rfid_antenna'])
			
			if not rfid_antenna:
				status = False
				status_entries.append(
					(_('RFID Antenna Configuration'), (
						_('RFID Antenna for Tag Read must be specified.'),
						_('Please specify the RFID Antenna.'),
					)),
				)
			else:
				status, response = ReadTag(rfid_antenna)
				# DEBUG DEBUG
				#status, response = True, {'tags': ['A7A2102303']}
				if not status:
					status_entries.append(
						(_('Tag Read Failure'), response.get('errors',[]) ),
					)
				else:
					tags = response.get('tags', [])
					try:
						tag = tags[0]
					except (AttributeError, IndexError) as e:
						status = False
						status_entries.append(
							(_('Tag Read Failure'), [e] ),
						)
				
				if tag and len(tags) > 1:
					status = False
					status_entries.append(
						(_('Multiple Tags Read'), tags ),
					)
			
			if not status:
				return render( request, 'license_holder_scan_rfid.html', locals() )
			
			request.session['license_holder_filter'] = u'rfid={}'.format(tag.lstrip('0'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = RfidScanForm( initial=dict(rfid_antenna=rfid_antenna) )
		
	return render( request, 'license_holder_scan_rfid.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def LicenseHoldersCorrectErrors( request ):
	license_holders = LicenseHolder.get_errors()
	isEdit = True
	return render( request, 'license_holder_correct_errors_list.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def LicenseHoldersAutoCreateTags( request, confirmed=False ):
	if confirmed:
		LicenseHolder.auto_create_tags()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Auto Create Tag Values for All License Holders')
	message = _("Create tag values for all License Holders.  If SystemInfo 'RFID Tag from License' is set, the tag will be created from the License Code.  Otherwise it will be created from the Database ID.")
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'LicenseHoldersAutoCreateTags/1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def LicenseHoldersManageDuplicates( request ):
	duplicates = LicenseHolder.get_duplicates()
	return render( request, 'license_holder_duplicate_list.html', locals() )

def GetLicenseHolderSelectDuplicatesForm( duplicates ):
	choices = [(lh.pk, u'{last_name}, {first_name} - {gender} - {date_of_birth} - {city} - {state_prov} - {nationality} - {license}'.format(
		last_name=lh.last_name,
		first_name=lh.first_name,
		gender=lh.get_gender_display(),
		date_of_birth=lh.date_of_birth,
		state_prov=lh.state_prov,
		city=lh.city,
		nationality=lh.nationality,
		license=lh.license_code, )) for lh in duplicates]
	
	@autostrip
	class LicenseHolderSelectDuplicatesForm( Form ):
		pks = forms.MultipleChoiceField( required = False, label = _('Potential Duplicates'), choices=choices )
		
		def __init__(self, *args, **kwargs):
			super(LicenseHolderSelectDuplicatesForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Field('pks', css_class = 'form-control', size = '10'),
				),
				Row(
					button_args[0],
					button_args[1],
				)
			)
	
	return LicenseHolderSelectDuplicatesForm
	
@access_validation()
def LicenseHoldersSelectDuplicates( request, duplicateIds ):
	pks = [int(pk) for pk in duplicateIds.split(',')]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = GetLicenseHolderSelectDuplicatesForm( duplicates )( request.POST )
		if form.is_valid():
			pks = form.cleaned_data['pks']
			return HttpResponseRedirect( '{}LicenseHoldersSelectMergeDuplicate/{}/'.format(getContext(request,'cancelUrl'), ','.join('{}'.format(pk) for pk in pks)) )
	else:
		form = GetLicenseHolderSelectDuplicatesForm( duplicates )( initial=dict(pks=pks) )
	return render( request, 'license_holder_select_duplicates.html', locals() )
	
@access_validation()
def LicenseHoldersSelectMergeDuplicate( request, duplicateIds ):
	pks = [int(pk) for pk in duplicateIds.split(',')]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	return render( request, 'license_holder_select_merge_duplicate.html', locals() )

@access_validation()
def LicenseHoldersMergeDuplicates( request, mergeId, duplicateIds ):
	license_holder_merge = get_object_or_404( LicenseHolder, pk=mergeId )
	pks = [int(pk) for pk in duplicateIds.split(',')]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	return render( request, 'license_holder_select_merge_duplicate_confirm.html', locals() )

def LicenseHoldersMergeDuplicatesOK( request, mergeId, duplicateIds ):
	license_holder_merge = get_object_or_404( LicenseHolder, pk=mergeId )
	pks = [int(pk) for pk in duplicateIds.split(',')]
	pks = [pk for pk in pks if pk != license_holder_merge.pk]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	license_holder_merge_duplicates( license_holder_merge, duplicates )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
#-----------------------------------------------------------------------
@access_validation()
def LicenseHolderNew( request ):
	return GenericNew( LicenseHolder, request, LicenseHolderForm,
		instance_fields={'license_code': 'TEMP'}
	)
	
@access_validation()
def LicenseHolderEdit( request, licenseHolderId ):
	return GenericEdit( LicenseHolder, request,
		licenseHolderId,
		LicenseHolderForm,
		template='license_holder_form.html',
	)
	
@access_validation()
def LicenseHolderDelete( request, licenseHolderId ):
	return GenericDelete( LicenseHolder, request,
		licenseHolderId,
		LicenseHolderForm,
		template='license_holder_form.html',
	)
	
#-----------------------------------------------------------------------

def GetFinishLynxResponse( competition ):
	zip = FinishLynxExport( competition )
	response = HttpResponse(zip, content_type="application/zip")
	response['Content-Disposition'] = 'attachment; filename={}-FinishLynx.zip'.format(
		utils.cleanFileName(competition.name),
	)
	return response	

def ApplyNumberSet( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	participants_changed = competition.apply_number_set()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

def InitializeNumberSet( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	competition.initialize_number_set()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@autostrip
class CompetitionSearchForm( Form ):
	year = forms.ChoiceField( required=False, label = _('Year') )
	discipline = forms.ChoiceField( required=False, label = _('Discipline') )
	search_text = forms.CharField( required=False, label = _('Search Text') )
	
	def __init__(self, *args, **kwargs):
		request = kwargs.pop('request', None)
		is_superuser = (request and request.user.is_superuser)
		
		super(CompetitionSearchForm, self).__init__(*args, **kwargs)
		
		if is_superuser:
			year_cur = datetime.datetime.now().year
			competitions = Competition.objects.all().order_by('start_date')
			competition = competitions.first()
			year_min = competition.start_date.year if competition else year_cur
			competition = competitions.last()
			year_max = competition.start_date.year if competition else year_cur
			self.fields['year'].choices = [(-1, '---')] + [(y,'{}'.format(y)) for y in xrange(year_max, year_min-1, -1)]
			
			disciplines = Discipline.objects.filter(
				pk__in=competitions.values_list('discipline',flat=True).distinct() ).order_by('sequence')
			self.fields['discipline'].choices = [(-1, '---')] + [(d.pk,d.name) for d in disciplines]
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('OK'), css_class = 'btn btn-warning' ),
		]
		
		if is_superuser:
			button_args.extend(	[
				Submit('new-submit', _('New Competition'), css_class = 'btn btn-success'),
				Submit('import-submit', _('Import Competition'), css_class = 'btn btn-primary'),
			] )
		
			self.helper.layout = Layout(
				Row(
					Field('year' ), HTML('&nbsp;'*2),
					Field('discipline' ), HTML('&nbsp;'*2),
					Field('search_text' ), HTML('&nbsp;'*2),
				),
				Row( *(button_args[:2] + [HTML('&nbsp;'*8)] + button_args[2:]) ),
			)
		else:
			self.helper.layout = Layout(
				Row(
					Field( 'year', type='hidden' ),
					Field( 'discipline', type='hidden' ),
					Field('search_text' ), HTML('&nbsp;'*4),
				),
				Row( *button_args[:2] ),
			)

	
def GetCompetitionForm( competition_cur = None ):
	@autostrip
	class CompetitionForm( ModelForm ):
		class Meta:
			model = Competition
			fields = '__all__'
			widgets = {
				'ftp_password': forms.PasswordInput(render_value=True),
			}

		def uploadPrereg( self, request, competition ):
			return HttpResponseRedirect( pushUrl(request, 'UploadPrereg', competition.id) )
		
		def autoGenerateMissingTags( self, request, competition ):
			participants_changed = competition.auto_generate_missing_tags()
			participants_changed_count = len(participants_changed)
			title = _('Tags Updated')
			return render( request, 'participants_changed.html', locals() )
			
		def applyNumberSet( self, request, competition ):
			page_title = _('Apply Number Set')
			message = _('This will overwrite participant bibs from the NumberSet.')
			target = pushUrl(request, 'ApplyNumberSet', competition.id)
			return render( request, 'are_you_sure.html', locals() )
			
		def initializeNumberSet( self, request, competition ):
			page_title = _('Initialize Number Set')
			message = _('This will initialize and replace the NumberSet using the Participant Bib Numbers from this Competition.')
			target = pushUrl(request, 'InitializeNumberSet', competition.id)
			return render( request, 'are_you_sure.html', locals() )
			
		def editReportTags( self, request, competition ):
			return HttpResponseRedirect( pushUrl(request,'ReportLabels') )
			
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			
			super(CompetitionForm, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.helper.layout = Layout(
				Row(
					Col(Field('name', size=40), 4),
					Col(Field('description', size=40), 4),
					Col('category_format', 4),
				),
				Row(
					Col(Field('city', size=40), 4),
					Col(Field('stateProv', size=40), 4),
					Col(Field('country', size=40), 4),
				),
				Row(
					Col(Field('organizer', size=40), 3),
					Col(Field('organizer_contact', size=40), 3),
					Col(Field('organizer_email', size=40), 3),
					Col(Field('organizer_phone', size=20), 3),
				),
				Row(
					Col('discipline', 2),
					Col('race_class', 2),
					Col('legal_entity', 4),
				),
				Row(
					Col('start_date', 2),
					Col('number_of_days', 2),
					Col('recurring', 2),
					Col('distance_unit', 2),
				),
				Row(
					Col('number_set', 4),
					Col('seasons_pass', 4),
				),
				Row(
					Col(Field('using_tags'), 4),
					Col(Field('use_existing_tags'), 4),
				),
				Row( HTML('<hr/>') ),
				Row(
					Col('ftp_host', 2),
					Col('ftp_user', 2),
					Col(Field('ftp_password', autocomplete='off'), 2),
					Col(Field('ftp_path', size=80), 6),
				),
				Row(
					Col('ftp_upload_during_race', 4),
				),
				Row( HTML('<hr/><strong>Number Print Options:</strong>') ),
				Row(
					Col(Field('bib_label_print'),2),
					Col(Field('bibs_label_print'),2),
					Col(Field('bibs_laser_print'),2),
					Col(Field('shoulders_label_print'),3),
					Col(Field('frame_label_print'),3),
				),
				Row( HTML('<hr/>') ),
				Row(
					Col(Field('report_labels',size=8), 2),
					Col('ga_tracking_id', 4),
					Col(Field('show_signature'),4),
				),
				Row( HTML('<hr/>') ),
			)
			
			self.additional_buttons = []
			if button_mask == EDIT_BUTTONS:
				self.additional_buttons.append(
					('upload-prereg-list-submit', _('Upload Prereg List'), 'btn btn-success', self.uploadPrereg),
				)
				self.additional_buttons.append(
					('edit-report-labels-submit', _('Edit Report Labels'), 'btn btn-primary', self.editReportTags),
				)
				
				if competition_cur and competition_cur.using_tags:
					self.additional_buttons.append(
						('auto-generate-missing-tags-submit', _('Auto Generate Missing Tags for Existing Participants'), 'btn btn-primary', self.autoGenerateMissingTags),
					)
				if competition_cur and competition_cur.number_set:
					self.additional_buttons.append(
						('apply-number-set-submit', _('Reapply NumberSet to Existing Participants'), 'btn btn-primary', self.applyNumberSet),
					)
					self.additional_buttons.append(
						('initialize-number-set-submit', _('Initialize NumberSet from Existing Participants'), 'btn btn-primary', self.initializeNumberSet),
					)
			
			addFormButtons( self, button_mask, additional_buttons=self.additional_buttons )
	
	return CompetitionForm
			
@access_validation()
def CompetitionsDisplay( request ):
	form = None
	search_fields = request.session.get('competition_filter', {})
	if not isinstance(search_fields, dict):
		search_fields = {}
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'CompetitionNew') )
		
		if 'import-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'CompetitionImport') )
		
		if request.user.is_superuser:
			form = CompetitionSearchForm( request.POST, request=request )
			if form.is_valid():
				request.session['competition_filter'] = search_fields = form.cleaned_data
	else:
		if request.user.is_superuser:
			form = CompetitionSearchForm( initial=search_fields, request=request )
	
	competitions = Competition.objects.all()
	
	if request.user.is_superuser:
		year = int( search_fields.get( 'year', -1 ) )
		if year >= 0:
			date_min = datetime.date( int(search_fields['year']), 1, 1 )
			date_max = datetime.date( int(search_fields['year'])+1, 1, 1 ) - datetime.timedelta(days=1)
			competitions = competitions.filter( start_date__range=(date_min, date_max) )
		
		dpk = int( search_fields.get( 'discipline', -1 ) )
		if dpk >= 0:
			competitions = competitions.filter( discipline__pk=dpk )
		
		if search_fields.get( 'search_text', None ):
			competitions = applyFilter( search_fields['search_text'], competitions, Competition.get_search_text )
	else:	
		# If not super user, only show the competitions for today and after.
		dNow = timezone.now().date()
		competitions = competitions.filter(start_date__gte = dNow - datetime.timedelta(days=365) )
		competitions = [c for c in competitions
			if c.start_date + datetime.timedelta(days=(c.number_of_days or 1)) > dNow
		]
	
	competitions = sorted( competitions, key = operator.attrgetter('start_date'), reverse=True )
	return render( request, 'competition_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionNew( request ):
	missing = []
	if not CategoryFormat.objects.count():
		missing.append( (_('No Category Formats defined.'), pushUrl(request,'CategoryFormats')) )
	if missing:
		return render( request, 'missing_elements.html', locals() )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = GetCompetitionForm()(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect( '{}CompetitionDashboard/{}/'.format(getContext(request,'cancelUrl'), instance.id) )
				
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'CompetitionEdit', instance.id, cancelUrl = True) )
	else:
		competition = Competition()
		# Initialize the category format to the first one.
		for category_format in CategoryFormat.objects.all():
			competition.category_format = category_format
			break
		form = GetCompetitionForm(competition)( instance = competition, button_mask = NEW_BUTTONS )
	
	return render( request, 'competition_form.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionEdit( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return GenericEdit(
		Competition, request, competitionId, GetCompetitionForm(competition),
		template = 'competition_form.html',
		additional_context = dict(events=competition.get_events(), category_numbers=competition.categorynumbers_set.all()),
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionCopy( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	recurring_start_date = competition.start_date + datetime.timedelta( days=competition.recurring ) if competition.recurring else None
	
	competition_new = competition.make_copy()
	competition_new.name = getCopyName( Competition, competition.name )
	competition_new.save()
	
	if recurring_start_date:
		competition_new.start_date = recurring_start_date
		competition_new.save()
	
	return HttpResponseRedirect(getContext(request, 'cancelUrl'))
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionDelete( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return GenericDelete(
		Competition, request, competitionId, GetCompetitionForm(competition),
		template = 'competition_form.html',
		additional_context = dict(events=competition.get_events()),
	)

@access_validation()
def CompetitionDashboard( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	events_mass_start = competition.get_events_mass_start()
	events_tt = competition.get_events_tt()
	category_numbers=competition.categorynumbers_set.all()
	
	comp_inuse = set()
	comp_lost = set()
	if competition.number_set:
		for bib, date_lost in competition.number_set.numbersetentry_set.values_list('bib','date_lost'):
			if date_lost:
				comp_lost.add( bib )
			else:
				comp_inuse.add( bib )
	comp_inuse |= set( competition.get_participants().values_list('bib', flat=True) )
	for c in category_numbers:
		cn = c.get_numbers()
		c.total_count = len(cn)
		c.inuse_count = len(cn & comp_inuse)
		c.lost_count = len(cn & comp_lost)
		c.onhand_count = c.total_count - c.inuse_count - c.lost_count
	
	return render( request, 'competition_dashboard.html', locals() )

def GetRegAnalyticsForm( competition ):
	class RegAnalyticsForm( Form ):
		finish_date = competition.finish_date
		d = competition.start_date
		dates = []
		while d <= finish_date:
			dates.append( d.strftime('%Y-%m-%d') )
			d += datetime.timedelta( days = 1 )
		
		day = forms.ChoiceField( required = True, choices=((d, d) for d in dates) )
		
		def __init__(self, *args, **kwargs):
			super(RegAnalyticsForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Field('day', cols = '60'),
				),
				Row(
					button_args[0],
					HTML( '&nbsp;' * 5 ),
					button_args[1],
				),
			)
	return RegAnalyticsForm
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionRegAnalytics( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = GetRegAnalyticsForm(competition)(request.POST)
		if form.is_valid():
			start = datetime.datetime( *[int(v) for v in form.cleaned_data['day'].replace('-', ' ').split()] )
	else:
		form = GetRegAnalyticsForm(competition)()
		start = datetime.datetime( *[int(v) for v in form.dates[0].replace('-', ' ').split()] )
	
	payload = AnalyzeLog( start=start, end=start + datetime.timedelta(hours=24) ) or {}
	payload['valid'] = bool(payload)
	payload['participant_total'] = Participant.objects.filter(competition=competition, role=Participant.Competitor,).count()
	payload['participant_prereg_total'] = Participant.objects.filter(competition=competition, role=Participant.Competitor, preregistered=True).count()
	payload['license_holder_total'] = len( set(Participant.objects.filter(competition=competition).values_list('license_holder__pk', flat=True)) )
	try:
		payload['transactionPeak'][0] = payload['transactionPeak'][0].strftime('%H:%M').lstrip('0')
	except:
		pass
	payload_json = json.dumps(payload, separators=(',',':'))
	logFileName = WriteLog.logFileName
	return render( request, 'reg_analytics.html', locals() )

@access_validation()
def TeamsShow( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	team_info = [ {
			'team':team,
			'team_name':team.name,
			'staff':Participant.objects.filter(competition=competition, team=team).exclude(role=Participant.Competitor).order_by('role'),
			'competitor_count':Participant.objects.filter(competition=competition, team=team, role=Participant.Competitor).count(),
			'competitors':Participant.objects.filter(competition=competition, team=team, role=Participant.Competitor).order_by('bib'),
		} for team in competition.get_teams() ]
	team_info.append(
		{
			'team_name':unicode(_('<<No Team>>')),
			'staff':[],
			'competitor_count':Participant.objects.filter(competition=competition, team__isnull=True, role=Participant.Competitor).count(),
			'competitors':Participant.objects.filter(competition=competition, team__isnull=True, role=Participant.Competitor).order_by('bib'),
		}
	)
	
	def getCategorySeq( p ):
		return p.category.sequence if p.category else -1
	
	for ti in team_info:
		ti['competitors'] = competitors = sorted(
			list(ti['competitors']),
			key=lambda p: (getCategorySeq(p), p.license_holder.search_text),
		)
		for i in xrange( 1, len(competitors) ):
			if getCategorySeq(competitors[i-1]) != getCategorySeq(competitors[i]):
				competitors[i].different_category = True
	
	num_teams = len(team_info)
	return render( request, 'teams_show.html', locals() )

@access_validation()
def FinishLynx( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return GetFinishLynxResponse( competition )

#-----------------------------------------------------------------------
@access_validation()
def CompetitionEventParticipationSummary( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )

#-----------------------------------------------------------------------
@access_validation()
def StartLists( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	events = competition.get_events()
	return render( request, 'start_lists.html', locals() )
	
@access_validation()
def StartList( request, eventId ):
	instance = get_object_or_404( EventMassStart, pk=eventId )
	time_stamp = datetime.datetime.now()
	page_title = u'{} - {}'.format( instance.competition.name, instance.name )
	return render( request, 'mass_start_start_list.html', locals() )
	
@access_validation()
def StartListTT( request, eventTTId ):
	instance = get_object_or_404( EventTT, pk=eventTTId )
	time_stamp = datetime.datetime.now()
	page_title = u'{} - {}'.format( instance.competition.name, instance.name )
	return render( request, 'tt_start_list.html', locals() )

def StartListExcelDownload( request, eventId, eventType ):
	eventType = int(eventType)
	if eventType == 0:
		event = get_object_or_404( EventMassStart, pk=eventId )
	elif eventType == 1:
		event = get_object_or_404( EventTT, pk=eventId )
	else:
		assert False, 'unknown event type: {}'.format(eventType)
	
	xl = get_start_list_excel( event )
	response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	response['Content-Disposition'] = 'attachment; filename=RaceDB-{}-{}_{}-{}.xlsx'.format(
		utils.cleanFileName(event.competition.name),	
		utils.cleanFileName(event.name),
		event.date_time.strftime('%Y-%m-%d-%H%M%S'),
		datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
	)
	return response

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def StartListEmails( request, eventId, eventType ):
	eventType = int(eventType)
	if eventType == 0:
		event = get_object_or_404( EventMassStart, pk=eventId )
	elif eventType == 1:
		event = get_object_or_404( EventTT, pk=eventId )
	else:
		assert False, 'unknown event type: {}'.format(eventType)
	
	return show_emails( request, participants=event.get_participants(), okUrl=getContext(request,'cancelUrl') )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionApplyOptionalEventChangesToExistingParticipants( request, competitionId, confirmed=False ):
	competition = get_object_or_404( Competition, pk=competitionId )
	if confirmed:
		competition.add_all_participants_to_default_events()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Apply Optional Event Defaults to Existing Participants')
	message = _('This will reapply Optional Events defaults to all existing Participants.  Participants will be added to "Select by Default" Optional Events and will be excluded from them otherwise.  If Participants have made previous choices regarding the events they are participating in, these will be overwritten.')
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'CompetitionApplyOptionalEventChangesToExistingParticipants/{}/{}/'.format(competition.id,1)
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
@autostrip
class UploadPreregForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx, *.xls)') )
	clear_existing = forms.BooleanField( required=False, label=_('Clear All Participants First'), help_text=_("Removes all existing Participants from the Competition before the Upload.  Use with Caution.") )
	
	def __init__( self, *args, **kwargs ):
		super( UploadPreregForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col( Field('excel_file', accept=".xls,.xlsx"), 8),
				Col( Field('clear_existing'), 4 ),
			),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_upload_prereg( competitionId, excel_contents, clear_existing ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO.StringIO()
	init_prereg(
		competitionId=competitionId,
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
		clear_existing=clear_existing,
	)
	results_str = message_stream.getvalue()
	return results_str

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def UploadPrereg( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = UploadPreregForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_upload_prereg( competitionId, request.FILES['excel_file'], form.cleaned_data['clear_existing'] )
			return render( request, 'upload_prereg.html', locals() )
	else:
		form = UploadPreregForm()
	
	return render( request, 'upload_prereg.html', locals() )

#-----------------------------------------------------------------------
@autostrip
class ImportExcelForm( Form ):
	excel_file = forms.FileField( required=True, label=_('Excel Spreadsheet (*.xlsx, *.xls)') )
	update_license_codes = forms.BooleanField( required=False, label=_('Update License Codes based on First Name, Last Name, Date of Birth match'),
			help_text=_('WARNING: Only check this if you wish to replace the License codes with new ones.  MAKE A BACKUP FIRST.  Be Careful!') )
	
	def __init__( self, *args, **kwargs ):
		super( ImportExcelForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Field('excel_file', accept=".xls,.xlsx"),
			),
			Row(
				Field('update_license_codes'),
			),
		)

		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_license_holder_import_excel( excel_contents, update_license_codes ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO.StringIO()
	license_holder_import_excel(
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
		update_license_codes=update_license_codes,
	)
	results_str = message_stream.getvalue()
	return results_str
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def LicenseHoldersImportExcel( request ):
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = ImportExcelForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_license_holder_import_excel( request.FILES['excel_file'], form.cleaned_data['update_license_codes'] )
			return render( request, 'license_holder_import_excel.html', locals() )
	else:
		form = ImportExcelForm()
	
	return render( request, 'license_holder_import_excel.html', locals() )

#-----------------------------------------------------------------------
@autostrip
class AdjustmentForm( Form ):
	est_speed = forms.CharField( max_length=6, required=False, widget=forms.TextInput(attrs={'class':'est_speed'}) )
	seed_option = forms.ChoiceField( choices=Participant.SEED_OPTION_CHOICES )
	adjustment = forms.CharField( max_length=6, required=False, widget=forms.TextInput(attrs={'class':'adjustment'}) )
	entry_tt_pk = forms.CharField( widget=forms.HiddenInput() )

class AdjustmentFormSet( formset_factory(AdjustmentForm, extra=0, max_num=100000) ):
	def __init__( self, *args, **kwargs ):
		if 'entry_tts' in kwargs:
			entry_tts = list( kwargs['entry_tts'] )
			del kwargs['entry_tts']
			super( AdjustmentFormSet, self ).__init__(
				initial=[{
					'est_speed':u'{:.3f}'.format(e.participant.competition.to_local_speed(e.participant.est_kmh)),
					'seed_option': e.participant.seed_option,
					'adjustment': '',
					'entry_tt_pk': unicode(e.pk),
				} for e in entry_tts]
			)
			
			# Get the waves for each participant.
			participant_wave = {}
			for event in set( ett.event for ett in entry_tts ):
				for wave in event.get_wave_set().all():
					for p in wave.get_participants_unsorted():
						participant_wave[p.pk] = wave
			
			# Add the entry_tt to each form to support the display.
			# Also add the wave.
			# Also add a flag when the time gap changes.
			tDelta = datetime.timedelta( seconds = 0 )
			for i, form in enumerate(self):
				form.entry_tt = entry_tts[i]
				form.wave = participant_wave.get(entry_tts[i].participant.pk, None)
				form.gap_change = 0
				if i > 0:
					tDeltaCur = entry_tts[i].start_time - entry_tts[i-1].start_time
					if tDeltaCur != tDelta:
						if i > 1:
							form.gap_change = 1 if tDeltaCur > tDelta else -1
						tDelta = tDeltaCur
		else:
			super( AdjustmentFormSet, self ).__init__( *args, **kwargs )

def SeedingEdit( request, eventTTId ):
	instance = get_object_or_404( EventTT, pk=eventTTId )
	if request.method == 'POST':
		adjustment_formset = AdjustmentFormSet( request.POST )
		reNum = re.compile( '[^0-9]' )
		if adjustment_formset.is_valid():
			def get_eda():
				''' Get the entry_tt, direction and adjustment for each line in the form. '''
				''' Also commit the est_speed to the entry. '''
				eda = []
				for d in adjustment_formset.cleaned_data:
					pk = d['entry_tt_pk']
					try:
						pk = int(pk)
					except ValueError:
						pass
					
					try:
						entry_tt = EntryTT.objects.get( pk=pk )
					except EntryTT.DoesNotExist:
						continue
					
					participant_changed = False
					
					try:
						est_kmh = entry_tt.participant.competition.to_kmh(float(d['est_speed']))
						if entry_tt.participant.est_kmh != est_kmh:
							entry_tt.participant.est_kmh = est_kmh
							participant_changed = True
					except ValueError:
						pass
					
					try:
						seed_option = d['seed_option']
						if entry_tt.participant.seed_option != seed_option:
							entry_tt.participant.seed_option = seed_option
							participant_changed = True
					except ValueError:
						pass
					
					if participant_changed:
						entry_tt.participant.save()
					
					adjustment = d['adjustment'].strip()
					if not adjustment:
						continue

					direction = adjustment[0] if adjustment[0] in ('+','-') else None
						
					try:
						adjustment = int( reNum.sub(u'', adjustment) )
					except ValueError:
						continue
					
					eda.append( (entry_tt, direction, adjustment) )
				return eda
			
			with transaction.atomic():
				eda = get_eda()
				if "apply_adjustments" in request.POST:
					for entry_tt, direction, adjustment in eda:
						if direction == '-':
							entry_tt.move_to( entry_tt.start_sequence - adjustment )
					for entry_tt, direction, adjustment in reversed(eda):
						if direction == '+':
							entry_tt.move_to( entry_tt.start_sequence + adjustment )
					
					eda.sort( key = lambda v: (v[2], v[0].start_sequence) )
					
					for entry_tt, direction, adjustment in eda:
						if direction is None and adjustment < entry_tt.start_sequence:
							entry_tt.move_to( adjustment )
					for entry_tt, direction, adjustment in reversed(eda):
						if direction is None and adjustment > entry_tt.start_sequence:
							entry_tt.move_to( adjustment )
				if "regenerate_start_times" in request.POST:
					instance.create_initial_seeding()
	
	instance.repair_seeding()
	entry_tts=list(instance.entrytt_set.all())
	for e in entry_tts:
		e.clock_time = instance.date_time + e.start_time
	adjustment_formset = AdjustmentFormSet( entry_tts=entry_tts )
	return render( request, 'seeding_edit.html', locals() )

def GenerateStartTimes( request, eventTTId ):
	instance = get_object_or_404( EventTT, pk=eventTTId )
	instance.create_initial_seeding()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------

@autostrip
class EventMassStartForm( ModelForm ):
	class Meta:
		model = EventMassStart
		fields = '__all__'
	
	def newWaveCB( self, request, eventMassStart ):
		return HttpResponseRedirect( pushUrl(request,'WaveNew',eventMassStart.id) )
	
	def applyToParticipantsCB( self, request, eventMassStart ):
		return HttpResponseRedirect( pushUrl(request,'EventApplyToExistingParticipants',eventMassStart.id) )
	
	def clean( self ):
		cleaned_data = super(EventMassStartForm, self).clean()
		competition = cleaned_data.get("competition")
		if competition:			
			date_time = cleaned_data.get("date_time")
			if not (competition.start_date <=
					date_time.date() <
					(competition.start_date + datetime.timedelta(days=competition.number_of_days))):
				raise forms.ValidationError(
					_('"Date Time" must be within the date(s) of the Competition: %(date_range_str)s.  See Competition "Start Date and "Number of Days".'),
					code='invalid',
					params={'date_range_str': competition.date_range_str},
				)
		return cleaned_data
	
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super(EventMassStartForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline hidden-print'
		
		self.helper.layout = Layout(
			Field( 'competition', type='hidden' ),
			Field( 'event_type', type='hidden' ),
			Field( 'option_id', type='hidden' ),
			Row(
				Col(Field('name', size=40), 6),
				Col(Field('date_time', size=24), 6),
			),
			Row(
				Col(Field('optional'), 6),
				Col(Field('select_by_default'), 6),
			),
			Row( Field('rfid_option') ),
			Row( Col(Field('road_race_finish_times'),4), Col(Field('dnsNoData'),4), Col(Field('win_and_out'),4) ),
			Row( Field('note', rows='4', cols='60') ),
		)
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
				('new-wave-submit', _('New Start Wave'), 'btn btn-success', self.newWaveCB),
			] )
			instance = getattr(self, 'instance', None)
			if instance and instance.optional and instance.competition.has_participants():
				self.additional_buttons.extend( [
					('apply-to-participants-submit', _('Apply Select by Default to Existing Participants'), 'btn btn-success', self.applyToParticipantsCB),
				] )
		addFormButtons( self, button_mask, self.additional_buttons, print_button = _('Print Waves') if button_mask == EDIT_BUTTONS else None )

@access_validation()
def EventMassStartDisplay( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'event_mass_start_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventMassStartNew( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = EventMassStartForm(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST or 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'EventMassStartEdit', instance.id, cancelUrl=True) )
	else:
		instance = EventMassStart(
			competition = competition,
			date_time = datetime.datetime.combine( competition.start_date, datetime.time(10, 0, 0) ),
		)
		form = EventMassStartForm( instance = instance, button_mask = NEW_BUTTONS )
	
	return render( request, 'event_mass_start_form.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventMassStartEdit( request, eventId ):
	return GenericEdit( EventMassStart, request, eventId, EventMassStartForm,
		template = 'event_mass_start_form.html'
	)

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventMassStartDelete( request, eventId ):
	return GenericDelete( EventMassStart, request, eventId, EventMassStartForm,
		template = 'event_mass_start_form.html',
	)

def EventMassStartCrossMgr( request, eventId ):
	eventMassStart = get_object_or_404( EventMassStart, pk=eventId )
	competition = eventMassStart.competition
	xl = get_crossmgr_excel( eventMassStart )
	response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	response['Content-Disposition'] = 'attachment; filename={}-{}-{}.xlsx'.format(
		eventMassStart.date_time.strftime('%Y-%m-%d'),
		utils.cleanFileName(competition.name),
		utils.cleanFileName(eventMassStart.name),
	)
	return response

@csrf_exempt
def UploadCrossMgr( request ):
	payload, response = None, {'errors':[], 'warnings':[]}
	if request.method == "POST":
		try:
			payload = json.loads( request.body.decode('utf-8') )
		except Exception as e:
			response['errors'].append( unicode(e) )
	else:
		response['errors'].append( u'Request must be of type POST with json payload.' )
	
	print 'UploadCrossMgr: processing...'
	if payload:
		response = read_results.read_results_crossmgr( payload )
	print 'UploadCrossMgr: Done.'
	return JsonResponse( response )

#-----------------------------------------------------------------------

def GetWaveForm( event_mass_start, wave = None ):
	@autostrip
	class WaveForm( ModelForm ):
		class Meta:
			model = Wave
			fields = '__all__'
			
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			
			super(WaveForm, self).__init__(*args, **kwargs)
			
			category_list = event_mass_start.get_categories_without_wave()
			
			if wave is not None and wave.pk is not None:
				category_list.extend( wave.categories.all() )
				category_list.sort( key = lambda c: c.sequence )
				self.fields['distance'].label = u'{} ({})'.format( _('Distance'), wave.distance_unit )
			
			categories_field = self.fields['categories']
			categories_field.choices = [(category.id, category.full_name()) for category in category_list]
			categories_field.label = _('Available Categories')
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline hidden-print'
			
			self.helper.layout = Layout(
				Field( 'event', type='hidden' ),
				Row(
					Col(Field('name', size=40), 4),
					Col(Field('max_participants'), 3),
				),
				Row(
					Col(Field('start_offset'), 2),
					Col(Field('distance'), 3),
					Col(Field('laps'), 3),
					Col(Field('minutes'), 3),
				),
				Row(
					Col(Field('categories', size=12, css_class='hidden-print'), 6),
					Col(Field('rank_categories_together'), 3),
				),
			)
			addFormButtons( self, button_mask )
			
	return WaveForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveNew( request, eventMassStartId ):
	event_mass_start = get_object_or_404( EventMassStart, pk=eventMassStartId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = GetWaveForm(event_mass_start)(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'WaveEdit', instance.id, cancelUrl = True) )
	else:
		wave = Wave( event = event_mass_start )
		waves_existing = list( event_mass_start.wave_set.all() )
		c = len( waves_existing )
		waveLetter = []
		while 1:
			waveLetter.append( string.ascii_uppercase[c % 26] )
			c //= 26
			if c == 0:
				break
		waveLetter.reverse()
		waveLetter = ''.join( waveLetter )
		wave.name = u'Wave' + u' ' + waveLetter
		if waves_existing:
			wave_last = waves_existing[-1]
			wave.start_offset = wave_last.start_offset + datetime.timedelta(seconds = 60.0)
			wave.distance = wave_last.distance
			wave.laps = wave_last.laps
			wave.minutes = wave_last.minutes
		form = GetWaveForm(event_mass_start, wave)(instance = wave, button_mask = NEW_BUTTONS)
	
	return render( request, 'wave_form.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveEdit( request, waveId ):
	wave = get_object_or_404( Wave, pk=waveId )
	return GenericEdit( Wave, request, waveId, GetWaveForm(wave.event, wave),
		template = 'wave_form.html'
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveDelete( request, waveId ):
	wave = get_object_or_404( Wave, pk=waveId )
	return GenericDelete( Wave, request, waveId, GetWaveForm(wave.event, wave),
		template = 'wave_form.html'
	)

#-----------------------------------------------------------------------

@autostrip
class EventTTForm( ModelForm ):
	class Meta:
		model = EventTT
		fields = '__all__'
	
	def newWaveTTCB( self, request, eventTT ):
		return HttpResponseRedirect( pushUrl(request,'WaveTTNew',eventTT.id) )
	
	def applyToParticipantsCB( self, request, eventMassStart ):
		return HttpResponseRedirect( pushUrl(request,'EventApplyToExistingParticipants',eventMassStart.id) )
	
	def clean( self ):
		cleaned_data = super(EventTTForm, self).clean()
		competition = cleaned_data.get("competition")
		if competition:			
			date_time = cleaned_data.get("date_time")
			if not (competition.start_date <=
					date_time.date() <
					(competition.start_date + datetime.timedelta(days=competition.number_of_days))):
				raise forms.ValidationError(
					_('"Date Time" must be within the date(s) of the Competition: %(date_range_str)s.  See Competition "Start Date and "Number of Days".'),
					code='invalid',
					params={'date_range_str': competition.date_range_str},
				)
		return cleaned_data
	
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		
		super(EventTTForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline hidden-print'
		
		self.helper.layout = Layout(
			Field( 'competition', type='hidden' ),
			Field( 'event_type', type='hidden' ),
			Field( 'option_id', type='hidden' ),
			Field( 'rfid_option', type='hidden' ),
			Row(
				Col(Field('name', size=40), 4),
				Col(Field('date_time', size=24), 4),
				Col(Field('create_seeded_startlist', size=40), 4),
			),
			Row(
				Col(Field('optional'), 6),
				Col(Field('select_by_default'), 6),
			),
			Row( Col(Field('road_race_finish_times'),4), Col(Field('dnsNoData'),4) ),
			Row( Field('note', rows='4', cols='60') ),
		)
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
				('new-wave-submit', _('New TT Wave'), 'btn btn-success', self.newWaveTTCB),
			] )
			instance = getattr(self, 'instance', None)
			if instance and instance.optional and instance.competition.has_participants():
				self.additional_buttons.extend( [
					('apply-to-participants-submit', _('Apply Select by Default to Existing Participants'), 'btn btn-success', self.applyToParticipantsCB),
				] )
		addFormButtons( self, button_mask, self.additional_buttons, print_button = _('Print Waves') if button_mask == EDIT_BUTTONS else None )

@access_validation()
def EventTTDisplay( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'event_tt_list.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventTTNew( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = EventTTForm(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST or 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'EventTTEdit', instance.id, cancelUrl=True) )
	else:
		instance = EventTT(
			competition = competition,
			date_time = datetime.datetime.combine( competition.start_date, datetime.time(10, 0, 0) ),
		)
		form = EventTTForm( instance = instance, button_mask = NEW_BUTTONS )
	
	return render( request, 'event_tt_form.html', locals() )
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventTTEdit( request, eventTTId ):
	return GenericEdit( EventTT, request, eventTTId, EventTTForm,
		template = 'event_tt_form.html'
	)

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventTTDelete( request, eventTTId ):
	return GenericDelete( EventTT, request, eventTTId, EventTTForm,
		template = 'event_tt_form.html',
	)

def EventTTCrossMgr( request, eventTTId ):
	eventTT = get_object_or_404( EventTT, pk=eventTTId )
	competition = eventTT.competition
	xl = get_crossmgr_excel_tt( eventTT )
	response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	response['Content-Disposition'] = 'attachment; filename={}-{}-{}.xlsx'.format(
		eventTT.date_time.strftime('%Y-%m-%d'),
		utils.cleanFileName(competition.name),
		utils.cleanFileName(eventTT.name),
	)
	return response

#-----------------------------------------------------------------------

def GetWaveTTForm( event_tt, wave_tt = None ):
	@autostrip
	class WaveTTForm( ModelForm ):
		class Meta:
			model = WaveTT
			fields = '__all__'

		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			
			super(WaveTTForm, self).__init__(*args, **kwargs)
			
			category_list = event_tt.get_categories_without_wave()
			
			if wave_tt is not None and wave_tt.pk is not None:
				category_list.extend( wave_tt.categories.all() )
				category_list.sort( key = lambda c: c.sequence )
				self.fields['distance'].label = u'{} ({})'.format( _('Distance'), wave_tt.distance_unit )
			
			categories_field = self.fields['categories']
			categories_field.choices = [(category.id, category.full_name()) for category in category_list]
			categories_field.label = _('Available Categories')
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline hidden-print'
			
			self.helper.layout = Layout(
				Field( 'event', type='hidden' ),
				Field( 'sequence', type='hidden' ),
				Row(
					Col(Field('name', size=40), 4),
					Col(Field('max_participants'), 3),
				),
				Row(
					Col(Field('distance'), 3),
					Col(Field('laps'), 3),
				),
				Row(
					Col(Field('gap_before_wave'), 3),
					Col(Field('regular_start_gap'), 3),
					Col(Field('fastest_participants_start_gap'), 3),
					Col(Field('num_fastest_participants'), 3),
				),
				Row(
					Col(Field('sequence_option'), 6),
				),
				Row(
					Col(Field('categories', size=12, css_class='hidden-print'), 6),
				),
			)
			addFormButtons( self, button_mask )
			
	return WaveTTForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveTTNew( request, eventTTId ):
	event_tt = get_object_or_404( EventTT, pk=eventTTId )
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = GetWaveTTForm(event_tt)(request.POST, button_mask = NEW_BUTTONS)
		if form.is_valid():
			instance = form.save()
			
			if 'ok-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'cancelUrl'))
			if 'save-submit' in request.POST:
				return HttpResponseRedirect( pushUrl(request, 'WaveTTEdit', instance.id, cancelUrl = True) )
	else:
		wave_tt = WaveTT( event = event_tt )
		wave_tts_existing = list( event_tt.wavett_set.all() )
		c = len( wave_tts_existing )
		wave_tt_letter = []
		while 1:
			wave_tt_letter.append( string.ascii_uppercase[c % 26] )
			c //= 26
			if c == 0:
				break
		wave_tt_letter.reverse()
		wave_tt_letter = ''.join( wave_tt_letter )
		wave_tt.name = u'WaveTT' + u' ' + wave_tt_letter
		if wave_tts_existing:
			wave_tt_last = wave_tts_existing[-1]
			wave_tt.distance = wave_tt_last.distance
			wave_tt.laps = wave_tt_last.laps
		form = GetWaveTTForm(event_tt, wave_tt)(instance=wave_tt, button_mask=NEW_BUTTONS)
	
	return render( request, 'wave_tt_form.html', locals() )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveTTEdit( request, waveTTId ):
	wave_tt = get_object_or_404( WaveTT, pk=waveTTId )
	return GenericEdit( WaveTT, request, waveTTId, GetWaveTTForm(wave_tt.event, wave_tt),
		template = 'wave_tt_form.html'
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveTTDelete( request, waveTTId ):
	wave_tt = get_object_or_404( WaveTT, pk=waveTTId )
	return GenericDelete( WaveTT, request, waveTTId, GetWaveTTForm(wave_tt.event, wave_tt),
		template = 'wave_tt_form.html'
	)

@transaction.atomic
def WaveTTSwapAdjacent( waveTT, swapBefore ):
	NormalizeSequence( WaveTT.objects.filter(event=waveTT.event) )
	try:
		waveTTAdjacent = WaveTT.objects.get(event=waveTT.event, sequence=waveTT.sequence + (-1 if swapBefore else 1) )
	except WaveTT.DoesNotExist:
		return
		
	waveTTAdjacent.sequence, waveTT.sequence = waveTT.sequence, waveTTAdjacent.sequence
	waveTTAdjacent.save()
	waveTT.save()

@access_validation()
def WaveTTDown( request, waveTTId ):
	waveTT = get_object_or_404( WaveTT, pk=waveTTId )
	WaveTTSwapAdjacent( waveTT, False )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
@access_validation()
def WaveTTUp( request, waveTTId ):
	waveTT = get_object_or_404( WaveTT, pk=waveTTId )
	WaveTTSwapAdjacent( waveTT, True )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def EventApplyToExistingParticipants( request, eventId, confirmed=False ):
	event = EventMassStart.objects.filter(pk=eventId).first() or EventTT.objects.filter(pk=eventId).first()
	assert event
	
	if confirmed:
		event.apply_optional_participants()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Apply Event Option Defaults to Existing Participants')
	message = _("This will reapply this Event's Option defaults to all existing Participants.  Participants will be added if \"Select by Default\" is selected, otherwise they will be excluded.  If Participants have made previous choices regarding this Event, these will be overwritten.")
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'EventApplyToExistingParticipants/{}/{}/'.format(event.id,1)
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantSearchForm( Form ):
	scan = forms.CharField( required=False, label = _('Scan Search'), help_text=_('Searches License and RFID Tag only') )
	event = forms.ChoiceField( required=False, label = _('Event'), help_text=_('For faster response, review one Event at a time') )
	name_text = forms.CharField( required=False, label = _('Name Text') )
	team_text = forms.CharField( required=False, label = _('Team Text') )
	bib = forms.IntegerField( required=False, min_value = -1 , label=_('Bib: (-1 to find NoBib)') )
	gender = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('Men')), (1, _('Women'))), initial = 2 )
	role_type = forms.ChoiceField( required=False, label = _('Role Type')  )
	category = forms.ChoiceField( required=False, label = _('Category') )
	
	city_text = forms.CharField( required=False, label = _('City') )
	state_prov_text = forms.CharField( required=False, label = _('State/Prov') )
	nationality_text = forms.CharField( required=False, label = _('Nationality') )
	
	confirmed = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Confirmed') )
	paid = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Paid') )
	
	complete = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Complete') )
	
	has_events = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('None')), (1, _('Some'))), label = _('Has Events') )
	
	eligible = forms.ChoiceField( required=False, choices = ((2, '----'), (0, _('No')), (1, _('Yes'))), label = _('Eligible') )
	
	def __init__(self, *args, **kwargs):
		competition = kwargs.pop( 'competition', None )
		super(ParticipantSearchForm, self).__init__(*args, **kwargs)
		
		if competition:
			self.fields['category'].choices = \
				[(-1, '----')] + [(-2, _('*** Missing ***'))] + [(category.id, category.code_gender) for category in competition.get_categories()]
			events = sorted( competition.get_events(), key = operator.attrgetter('date_time') )
			self.fields['event'].choices = \
				[(u'-1.0', _('All'))] + [(u'{}.{}'.format(event.event_type, event.id), u'{} {}'.format(event.short_name, timezone.localtime(event.date_time).strftime('%Y-%m-%d %H:%M:%S'))) for event in events]
			
		roleChoices = [(i, role) for i, role in enumerate(Participant.ROLE_NAMES)]
		roleChoices[0] = (0, '----')
		self.fields['role_type'].choices = roleChoices
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline search'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'clear-submit', _('Clear Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('OK'), css_class = 'btn btn-primary' ),
			Submit( 'emails-submit', _('Emails'), css_class = 'btn btn-primary' ),
			Submit( 'export-excel-submit', _('Export to Excel'), css_class = 'btn btn-primary' ),
		]
		
		self.helper.layout = Layout(
			Row( Field('scan', size=20, autofocus=True ), HTML('&nbsp;'*8), Field('event'),),
			Row( Field('name_text'), Field('team_text'), Field('bib'), Field('gender'), Field('role_type'), Field('category'), ),
			Row( Field('city_text'), Field('state_prov_text'), Field('nationality_text'), Field('confirmed'),
				Field('paid'), Field('complete'), Field('has_events'), Field('eligible'), ),
			Row( *(button_args[:-2] + [HTML('&nbsp;'*8)] + button_args[-2:]) ),
		)

@access_validation()
def Participants( request, competitionId ):
	ParticipantsPerPage = 25
	
	competition = get_object_or_404( Competition, pk=competitionId )
	
	pfKey = 'participant_filter_{}'.format( competitionId )
	pageKey = 'participant_filter_page_{}'.format( competitionId )
	participant_filter = request.session.get(pfKey, {})
	
	def getPaginator( participants ):
		paginator = Paginator( participants, ParticipantsPerPage )
		page = request.GET.get('page',None) or request.session.get(pageKey,None)
		try:
			participants = paginator.page(page)
		except PageNotAnInteger:
			# If page is not an integer, deliver first page.
			page = 1
			participants = paginator.page(page)
		except EmptyPage:
			# If page is out of range (e.g. 9999), deliver last page of results.
			page = paginator.num_pages
			participants = paginator.page(page)
		request.session[pageKey] = page
		return participants, paginator
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'clear-submit' in request.POST:
			request.session[pfKey] = {}
			request.session[pageKey] = None
			return HttpResponseRedirect(getContext(request,'path'))
			
		form = ParticipantSearchForm( request.POST, competition=competition )
		if form.is_valid():
			participant_filter = form.cleaned_data
			request.session[pfKey] = participant_filter
			
			participant_filter_no_scan = participant_filter.copy()
			participant_filter_no_scan.pop( 'scan' )
			
			request.session[pfKey] = participant_filter_no_scan
			request.session[pageKey] = None
	else:
		form = ParticipantSearchForm( competition = competition, initial = participant_filter )
	
	#-------------------------------------------------------------------
	
	event = None
	try:
		event_type, event_pk = [int(v) for v in participant_filter.get('event', '-1.0').split('.')]
	except:
		event_type, event_pk = None, None
	if event_type == 0:
		event = competition.eventmassstart_set.filter(pk=event_pk).first()
	elif event_type == 1:
		event = competition.eventtt_set.filter(pk=event_pk).first()
			
	participants = event.get_participants() if event else competition.participant_set.all()
	
	competitors = participants.filter( role=Participant.Competitor )
	missing_category_count = competitors.filter( category__isnull=True ).count()
	missing_bib_count = competitors.filter( bib__isnull=True ).count()
	
	if participant_filter.get('scan',0):
		name_text = utils.normalizeSearch( participant_filter['scan'] )
		names = name_text.split()
		if names:
			q = Q()
			for n in names:
				q |= Q(license_holder__search_text__contains = n)
			participants = participants.filter( q ).select_related('team', 'license_holder')
			participants, paginator = getPaginator( participants )
			return render( request, 'participant_list.html', locals() )
	
	if participant_filter.get('bib',None) is not None:
		bib = participant_filter['bib']
		if bib <= 0:
			participants = participants.filter( bib__isnull=True )
		else:
			participants = participants.filter( bib=bib )
	
	role_type = int(participant_filter.get('role_type',0))
	if role_type > 0:
		participants = participants.filter( role__range=(100*role_type, 100*role_type+99) )
	
	if 0 <= int(participant_filter.get('gender',-1)) <= 1:
		participants = participants.filter( license_holder__gender=participant_filter['gender'])
	
	category_id = int(participant_filter.get('category',-1))
	if category_id > 0:
		participants = participants.filter( category__id=category_id )
	elif category_id == -2:
		participants = participants.filter( category__isnull=True )
		
	if 0 <= int(participant_filter.get('confirmed',-1)) <= 1:
		participants = participants.filter( confirmed=bool(int(participant_filter['confirmed'])) )
	
	if 0 <= int(participant_filter.get('paid',-1)) <= 1:
		participants = participants.filter( paid=bool(int(participant_filter['paid'])) )
	
	if 0 <= int(participant_filter.get('eligible',-1)) <= 1:
		participants = participants.filter( license_holder__eligible=bool(int(participant_filter['eligible'])) )
	
	participants = participants.select_related('team', 'license_holder')
	
	object_checks = []

	if participant_filter.get('name_text','').strip():
		name_text = utils.normalizeSearch( participant_filter['name_text'] )
		names = name_text.split()
		if names:
			for n in names:
				participants = participants.filter( license_holder__search_text__contains=n )
			def name_filter( p ):
				lh_name = utils.removeDiacritic(p.license_holder.full_name()).lower()
				return all(n in lh_name for n in names)
			object_checks.append( name_filter )

	# Create a search function so we get a closure for the search text in the iterator.
	def search_license_holder( search_text, field ):
		search_fields = utils.normalizeSearch( search_text ).split()
		if search_fields:
			object_checks.append( lambda p: utils.matchSearchFields(search_fields, getattr(p.license_holder, field)) )
		
	for field in ('city', 'state_prov', 'nationality'):
		search_field = field + '_text'
		if participant_filter.get(search_field,'').strip():
			search_license_holder(
				participant_filter[search_field],
				field
			)
	
	team_search = participant_filter.get('team_text','').strip()
	if team_search:
		participants = participants.filter( team__isnull = False )
		q = Q()
		for t in team_search.split():
			q &= Q( team__search_text__contains=t )
		participants = participants.filter( q )
		
	if 0 <= int(participant_filter.get('complete',-1) or 0) <= 1:
		complete = bool(int(participant_filter['complete']))
		if complete:
			participants = participants.filter( Participant.get_can_start_query(competition) )
		else:
			participants = participants.exclude( Participant.get_can_start_query(competition) )
		object_checks.append( lambda p: bool(p.is_done) == complete )
	
	has_events = int(participant_filter.get('has_events',-1))
	if has_events == 0:
		participants = participants.filter( role = Participant.Competitor )
		object_checks.append( lambda p: not p.has_any_events() )
	elif has_events == 1:
		object_checks.append( lambda p: p.has_any_events() )
	
	if object_checks:
		failed = [p for p in participants if not all(oc(p) for oc in object_checks)]
		if failed:
			participants = participants.exclude( pk__in=[p.pk for p in failed][:800] )

	if request.method == 'POST':
		if 'export-excel-submit' in request.POST:
			xl = get_participant_excel( Q(pk__in=participants.values_list('pk',flat=True)) )
			response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
			response['Content-Disposition'] = 'attachment; filename=RaceDB-Participants-{}.xlsx'.format(
				datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
			)
			return response
		if 'emails-submit' in request.POST:
			return show_emails( request, participants=participants )
			
	participants, paginator = getPaginator( participants )
	return render( request, 'participant_list.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantsInEvents( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	competition_events = sorted( competition.get_events(), key=lambda e: e.date_time )
	event_participants = {}
	for event in competition_events:
		p = event.get_participants()
		event_participants[event] = p
	
	participants = sorted( set.union(*[p for p in event_participants.itervalues()]), key=lambda p: p.license_holder.search_text )
	
	check_codes = {
		'optional_selected':	u"\u2611",
		'optional_deselected':	u"\u2610",
		'default_selected':		u"\u2713",
		'unavailable':			u"",
	}
	for participant in participants:
		event_status = []
		for event in competition_events:
			if participant in event_participants[event]:
				event_status.append( check_codes['optional_selected' if event.optional else 'default_selected'] )
			elif event.optional:
				event_status.append( check_codes['optional_deselected'] )
			else:
				event_status.append( check_codes['unavailable'] )
		participant.event_status = event_status
	
	return render( request, 'participants_in_events.html', locals() )

#-----------------------------------------------------------------------

@access_validation()
def ParticipantManualAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	search_text = request.session.get('participant_new_filter', '')
	btns = [('new-submit', 'New License Holder', 'btn btn-success')]
	add_by_manual = True
	if request.method == 'POST':
	
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		if 'new-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'LicenseHolderNew') )
			
		form = SearchForm( btns, request.POST, hide_cancel_button=True )
		if form.is_valid():
			search_text = form.cleaned_data['search_text']
			request.session['participant_new_filter'] = search_text
	else:
		form = SearchForm( btns, initial = {'search_text': search_text}, hide_cancel_button=True )
	
	search_text = utils.normalizeSearch( search_text )
	q = Q( active = True )
	for term in search_text.split():
		q &= Q(search_text__contains = term)
	license_holders = LicenseHolder.objects.filter(q).order_by('search_text')[:MaxReturn]
	
	# Flag which license_holders are already entered in this competition.
	license_holders_in_competition = set( p.license_holder.id
		for p in Participant.objects.select_related('license_holder').filter(competition=competition) )
	
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	return render( request, 'participant_add_list.html', locals() )

@access_validation()
def ParticipantAddToCompetition( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	
	participant = Participant( competition=competition, license_holder=license_holder, preregistered=False ).init_default_values().auto_confirm()
	
	try:
		# Fails if the license_holder is non-unique.
		participant.save()
		participant.add_to_default_optional_events()
	except IntegrityError as e:
		# Recover silently by going directly to edit screen with the existing participant.
		participant = Participant.objects.filter( competition=competition, license_holder=license_holder ).first()
		
	return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))

@access_validation()
def ParticipantAddToCompetitionDifferentCategory( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder, category__isnull=True ).first()
	if participant:
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder ).first()
	if participant:
		participant.id = None
		participant.category = None
		participant.role = Participant.Competitor
		participant.bib = None
		participant.save()
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	return ParticipantAddToCompetition( request, competitionId, licenseHolderId )

@access_validation()
def ParticipantAddToCompetitionDifferentCategoryConfirm( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	competition_age = competition.competition_age( license_holder )
	
	participant = Participant.objects.filter( competition=competition, license_holder=license_holder, category__isnull=True ).first()
	if participant:
		return HttpResponseRedirect('{}ParticipantEdit/{}/'.format(getContext(request,'pop2Url'), participant.id))
	
	return render( request, 'participant_add_to_category_confirm.html', locals() )

@access_validation()
def ParticipantEdit( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	system_info = SystemInfo.get_singleton()
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	competition_age = participant.competition.competition_age( participant.license_holder )
	is_suspicious_age = not (8 <= competition_age <= 90)
	isEdit = True
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	return render( request, 'participant_form.html', locals() )
	
@access_validation()
def ParticipantEditFromLicenseHolder( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	participant = Participant.objects.filter(competition=competition, license_holder=license_holder).first()
	if not participant:
		return ParticipantAddToCompetition( request, competitionId, licenseHolderId )
	return ParticipantEdit( request, participant.id )
	
@access_validation()
def ParticipantRemove( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	add_multiple_categories = request.user.is_superuser or SystemInfo.get_singleton().reg_allow_add_multiple_categories
	competition_age = participant.competition.competition_age( participant.license_holder )
	is_suspicious_age = not (8 <= competition_age <= 90)
	isEdit = False
	return render( request, 'participant_form.html', locals() )
	
@access_validation()
def ParticipantDoDelete( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	participant.delete()
	return HttpResponseRedirect( getContext(request,'cancelUrl') )

def get_temp_print_filename( request, bib, ftype ):
	port = request.META['SERVER_PORT']
	rfid_antenna = int(request.session.get('rfid_antenna',0))
	major_delimiter = '_'
	minor_delimiter = '-'
	return os.path.join(
		os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
		'pdfs',
		'{}{}{}'.format(
			major_delimiter.join( '{}{}{}'.format(attr, minor_delimiter, value)
				for attr, value in (('bib',bib), ('port',port), ('antenna',rfid_antenna), ('type',ftype)) ),
			
			major_delimiter, uuid.uuid4().hex
		)
	) + '.pdf'

def get_cmd( cmd ):
	if cmd.strip().startswith('$gswin'):
		return cmd.replace('$gswin', gs_cmd() or 'gs_not_found', 1)
	return cmd
	
@access_validation()
def ParticipantPrintBibLabels( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	system_info = SystemInfo.get_singleton()
	pdf_str = print_bib_tag_label( participant )
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, 'Frame' )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_str )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_str )
		except Exception as e:
			stdout_info, stderr_info = '', e
		
		try:
			os.remove( tmp_file )
		except:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_str, content_type="application/pdf")
		response['Content-Disposition'] = 'inline'
		return response
	else:
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	
@access_validation()
def ParticipantPrintBodyBib( request, participantId, copies=2, onePage=False ):
	participant = get_object_or_404( Participant, pk=participantId )
	system_info = SystemInfo.get_singleton()
	pdf_str = print_body_bib( participant, copies, onePage )
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, 'Body' )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_str )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_str )
		except Exception as e:
			stdout_info, stderr_info = '', e
		
		try:
			os.remove( tmp_file )
		except:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_str, content_type="application/pdf")
		response['Content-Disposition'] = 'inline'
		return response
	else:
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	
@access_validation()
def ParticipantPrintShoulderBib( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	system_info = SystemInfo.get_singleton()
	pdf_str = print_shoulder_bib( participant )
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, 'Shoulder' )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_str )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_str )
		except Exception as e:
			stdout_info, stderr_info = '', e
		
		try:
			os.remove( tmp_file )
		except:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_str, content_type="application/pdf")
		response['Content-Disposition'] = 'inline'
		return response
	else:
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	
@access_validation()
def ParticipantPrintEmergencyContactInfo( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	system_info = SystemInfo.get_singleton()
	pdf_str = print_id_label( participant )
	if system_info.print_tag_option == SystemInfo.SERVER_PRINT_TAG:
		try:
			tmp_file = get_temp_print_filename( request, participant.bib, 'Emergency' )
			with open(tmp_file, 'wb') as f:
				f.write( pdf_str )
			p = Popen(
				get_cmd(system_info.server_print_tag_cmd).replace('$1', tmp_file), shell=True, bufsize=-1,
				stdin=PIPE, stdout=PIPE, stderr=PIPE,
			)
			stdout_info, stderr_info = p.communicate( pdf_str )
		except Exception as e:
			stdout_info, stderr_info = '', e
		
		try:
			os.remove( tmp_file )
		except:
			pass
		
		title = _("Print Status")
		return render( request, 'cmd_response.html', locals() )
	elif system_info.print_tag_option == SystemInfo.CLIENT_PRINT_TAG:
		response = HttpResponse(pdf_str, content_type="application/pdf")
		response['Content-Disposition'] = 'inline'
		return response
	else:
		return HttpResponseRedirect( getContext(request,'cancelUrl') )
	
@autostrip
class ParticipantCategorySelectForm( Form ):
	gender = forms.ChoiceField( choices = (
									(-1, _('All')),
									(0, _('Men / Open')),
									(1, _('Women / Open')),
									(2, _('Open')),
								),
								initial = -1 )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantCategorySelectForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			HTML( u'{}:&nbsp;&nbsp;&nbsp;&nbsp;'.format( _("Search") ) ),
			Div( Field('gender', css_class = 'form-control'), css_class = 'form-group' ),
			HTML( u'&nbsp;&nbsp;&nbsp;&nbsp;' ),
			button_args[0],
			button_args[1],
		)

@access_validation()
def ParticipantCategoryChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	competition_age = competition.competition_age( license_holder )
	
	gender = None
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = ParticipantCategorySelectForm( request.POST )
		if form.is_valid():
			gender = int(form.cleaned_data['gender'])
	else:
		gender = license_holder.gender
		form = ParticipantCategorySelectForm( initial = dict(gender=gender) )
	
	categories = Category.objects.filter( format=competition.category_format )
	if gender == None:
		gender = license_holder.gender
	if gender != -1:
		categories = categories.filter( Q(gender=2) | Q(gender=gender) )
	available_categories = set( competition.get_available_categories(license_holder, gender=gender, participant_exclude=participant) )
	
	categories_with_numbers = set()
	for cn in CategoryNumbers.objects.filter( competition=competition ):
		if cn.get_numbers():
			categories_with_numbers |= set( cn.categories.all() )
	
	return render( request, 'participant_category_select.html', locals() )	

@access_validation()
def ParticipantCategorySelect( request, participantId, categoryId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	if int(categoryId):
		category = get_object_or_404( Category, pk=categoryId )
	else:
		category = None
	
	categories = set()
	for p in Participant.objects.filter(competition=competition, license_holder=participant.license_holder):
		if p != participant and participant.category:
			categories.add( participant.category )
	if competition.is_category_conflict(categories):
		has_error, conflict_explanation, conflict_participant = True, _('Cannot assign to another Category that already exists in an Event.'), None
		return render( request, 'participant_integrity_error.html', locals() )
	
	category_changed = (participant.category != category)
	participant.category = category
	if category and participant.role != Participant.Competitor:
		participant.role = Participant.Competitor
	
	participant.update_bib_new_category()
	
	try:
		participant.auto_confirm().save()
	except IntegrityError:
		has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
		return render( request, 'participant_integrity_error.html', locals() )

	if category_changed:
		participant.add_to_default_optional_events()
	return HttpResponseRedirect(getContext(request,'pop2Url'))

#-----------------------------------------------------------------------
@access_validation()
def ParticipantRoleChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	return render( request, 'participant_role_select.html', locals() )

@access_validation()
def ParticipantRoleSelect( request, participantId, role ):
	participant = get_object_or_404( Participant, pk=participantId )
	participant.role = int(role)
	if participant.role != Participant.Competitor:
		participant.bib = None
		participant.category = None
		if participant.role >= 200:			# Remove team for non-team roles.
			participant.team = None
	else:
		participant.init_default_values()
	participant.auto_confirm().save()
	return HttpResponseRedirect(getContext(request,'pop2Url'))
	
#-----------------------------------------------------------------------
@access_validation()
def ParticipantBooleanChange( request, participantId, field ):
	participant = get_object_or_404( Participant, pk=participantId )
	setattr( participant, field, not getattr(participant, field) )
	if field != 'confirmed':
		participant.auto_confirm()
	participant.save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
#-----------------------------------------------------------------------

@access_validation()
def ParticipantTeamChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
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
	q = Q( active=True )
	for n in search_text.split():
		q &= Q( search_text__contains = n )
	teams = Team.objects.filter(q)[:MaxReturn]
	return render( request, 'participant_team_select.html', locals() )
	
@access_validation()
def ParticipantTeamSelect( request, participantId, teamId ):
	participant = get_object_or_404( Participant, pk=participantId )
	if int(teamId):
		team = get_object_or_404( Team, pk=teamId )
	else:
		team = None
	participant.team = team
	participant.auto_confirm().save()
	return HttpResponseRedirect(getContext(request,'pop2Url'))

#-----------------------------------------------------------------------
class Bib( object ):
	def __init__( self, bib, license_holder = None, date_lost=None ):
		self.bib = bib
		self.license_holder = license_holder
		self.full_name = license_holder.full_name() if license_holder else ''
		self.date_lost = date_lost

@access_validation()
def ParticipantBibChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	if not participant.category:
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	competition = participant.competition
	category = participant.category
	
	# Find the available category numbers.
	participants = Participant.objects.filter( competition=competition )
	
	category_numbers = competition.get_category_numbers( category )
	if category_numbers:
		participants.filter( category__in=category_numbers.categories.all() )
	participants.select_related('license_holder')
	allocated_numbers = { p.bib: p.license_holder for p in participants }
	
	# Exclude existing bib numbers of all license holders if using existing bibs.
	# For duplicate license holders, chech whether the duplicate has ever races this category before.
	# We don't know whether the existing license holders will show up.
	if competition.number_set:
		current_bibs = defaultdict( set )
		nses = competition.number_set.numbersetentry_set.filter(date_lost__isnull=True)
		if category_numbers:
			nses = nses.filter( category_numbers.get_bib_query() )
		for nse in nses.select_related('license_holder'):
			current_bibs[nse.license_holder].add( nse.bib )
		
		pprevious = Participant.objects.filter( competition__number_set=competition.number_set, category=participant.category )
		if category_numbers:
			pprevious = pprevious.filter( category_numbers.get_bib_query() )
		for p in pprevious.exclude(license_holder=participant.license_holder).select_related('license_holder'):
			try:
				if p.bib in current_bibs[p.license_holder]:
					allocated_numbers.update[p.bib] = p.license_holder
			except:
				pass
		
		bib_available_all = competition.number_set.get_bib_available_all()
		nses = competition.number_set.numbersetentry_set.exclude(date_lost__isnull=True)
		if category_numbers:
			nses = nses.filter( category_numbers.get_bib_query() )
		lost_bibs = { bib:date_lost
			for bib, date_lost in nses.order_by('date_lost').values_list('bib','date_lost')
				if bib_available_all[bib] == 0
		}
	else:
		lost_bibs = {}
		
	if category_numbers:
		available_numbers = sorted( category_numbers.get_numbers() )
		category_numbers_defined = True
	else:
		available_numbers = []
		category_numbers_defined = False
	
	bibs = [Bib(n, allocated_numbers.get(n, None), lost_bibs.get(n,None)) for n in available_numbers]
	del available_numbers
	del allocated_numbers
	del lost_bibs
	
	if participant.category:
		bib_participants = { p.bib:p
			for p in Participant.objects.filter(competition=competition, category=participant.category).exclude(bib__isnull=True)
		}
		for b in bibs:
			try:
				b.full_name = bib_participants[b.bib].full_name_team
			except:
				pass
	
	has_existing_number_set_bib = (
		competition.number_set and
		participant.bib == competition.number_set.get_bib( competition, participant.license_holder, participant.category )
	)
	return render( request, 'participant_bib_select.html', locals() )
	
@access_validation()
def ParticipantBibSelect( request, participantId, bib ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	
	done = HttpResponseRedirect(getContext(request,'pop2Url'))
	showSelectAgain = HttpResponseRedirect(getContext(request,'popUrl'))
	
	bib_save = participant.bib
	bib = int(bib)
	
	if competition.number_set and bib_save is not None:
		def set_lost():
			competition.number_set.set_lost( bib_save, participant.license_holder )
	else:
		def set_lost():
			pass
	
	# No change - nothing to do.
	if bib == bib_save:
		return done
	
	# Bib assigned "No Bib".
	if bib < 0:
		participant.bib = None
		set_lost()
		return done		
	
	# Assign new Bib.
	participant.bib = bib
	
	# Check for conflict in events.
	if participant.category:
		bib_conflicts = participant.get_bib_conflicts()
		if bib_conflicts:
			# If conflict, restore the previous bib and repeat.
			participant.bib = bib_save
			return showSelectAgain

	set_lost()
	
	try:
		participant.auto_confirm().save()
	except IntegrityError as e:
		return showSelectAgain
	
	return done

#-----------------------------------------------------------------------
@autostrip
class ParticipantNoteForm( Form ):
	note = forms.CharField( widget = forms.Textarea, required = False, label = _('Note') )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantNoteForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row(
				Field('note', css_class = 'form-control', cols = '60'),
			),
			Row(
				button_args[0],
				button_args[1],
			)
		)
		
@access_validation()
def ParticipantNoteChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantNoteForm( request.POST )
		if form.is_valid():
			note = form.cleaned_data['note']
			participant.note = note
			participant.auto_confirm().save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantNoteForm( initial = dict(note = participant.note) )
		
	return render( request, 'participant_note_change.html', locals() )

@access_validation()
def ParticipantGeneralNoteChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantNoteForm( request.POST )
		if form.is_valid():
			note = form.cleaned_data['note']
			license_holder.note = note
			license_holder.save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantNoteForm( initial = dict(note = license_holder.note) )
		
	return render( request, 'participant_note_change.html', locals() )

#-----------------------------------------------------------------------

def GetParticipantOptionForm( participation_optional_events ):
	choices = [(event.option_id, u'{} ({})'.format(event.name, event.get_event_type_display()))
					for event, is_participating in participation_optional_events]
	
	@autostrip
	class ParticipantOptionForm( Form ):
		options = forms.MultipleChoiceField( required = False, label = _('Optional Events'), choices=choices )
		
		def __init__(self, *args, **kwargs):
			super(ParticipantOptionForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Field('options', css_class = 'form-control', size = '20'),
				),
				Row(
					button_args[0],
					button_args[1],
				)
			)
	
	return ParticipantOptionForm
		
@access_validation()
def ParticipantOptionChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	participation_events = participant.get_participant_events()
	participation_optional_events = [(event, is_participating) for event, optional, is_participating in participation_events if optional]
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = GetParticipantOptionForm( participation_optional_events )( request.POST )
		if form.is_valid():
			options = form.cleaned_data['options']
			ParticipantOption.set_option_ids( participant, options )
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = GetParticipantOptionForm( participation_optional_events )(
			initial = dict(options = [event.option_id for event, is_participating in participation_optional_events if is_participating])
		)
		
	return render( request, 'participant_option_change.html', locals() )
	
#-----------------------------------------------------------------------

def GetParticipantEstSpeedForm( competition ):
	@autostrip
	class ParticipantEstSpeedForm( Form ):
		est_speed = forms.FloatField( required = False,
			label=string_concat(_('Estimated speed for Time Trial'), ' (', competition.speed_unit_display, ')'),
			help_text=_('Enter a value or choose from the grid below.')
		)
		seed_option = forms.ChoiceField( required = False, choices=Participant.SEED_OPTION_CHOICES, label=_('Seed Option'),
			help_text=_('Tells RaceDB to start this rider as Early or as Late as possible in the Start Wave')
		)
		
		def __init__(self, *args, **kwargs):
			super(ParticipantEstSpeedForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'navbar-form navbar-left'
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					Col(Field('est_speed', css_class = 'form-control', size = '20'), 5),
					Col(Field('seed_option'), 6),
				),
				Row(
					button_args[0],
					button_args[1],
				)
			)
	
	return ParticipantEstSpeedForm
		
@access_validation()
def ParticipantEstSpeedChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = GetParticipantEstSpeedForm(competition)( request.POST )
		if form.is_valid():
			est_speed = form.cleaned_data['est_speed']
			participant.est_kmh = competition.to_kmh( est_speed or 0.0 )
			participant.seed_option = form.cleaned_data['seed_option']
			participant.save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = GetParticipantEstSpeedForm(competition)(
			initial = dict( est_speed=competition.to_local_speed(participant.est_kmh), seed_option=participant.seed_option )
		)
	
	speed_rc = {}
	if competition.distance_unit == 0:
		for col, kmh in enumerate(xrange(20, 51)):
			for row, decimal in enumerate(xrange(0, 10)):
				speed_rc[(col, row)] = u'{}.{:01d}'.format(kmh, decimal)
	else:
		for col, mph in enumerate(xrange(12, 32)):
			for row, decimal in enumerate(xrange(0, 10)):
				speed_rc[(col, row)] = u'{}.{:01d}'.format(mph, decimal)
	
	row_max = max( row for row, col in speed_rc.iterkeys() ) + 1
	col_max = max( col for row, col in speed_rc.iterkeys() ) + 1
	
	speed_table = [ [ speed_rc[(row, col)] for col in xrange(col_max) ] for row in xrange(row_max) ]
	speed_table.reverse()
	
	return render( request, 'participant_est_speed_change.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantWaiverForm( Form ):
	def __init__(self, *args, **kwargs):
		super(ParticipantWaiverForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Waiver Correct and Signed'), css_class = 'btn btn-success' ),
			Submit( 'not-ok-submit', _('Waiver Incorrect or Unsigned'), css_class = 'btn btn-danger' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		
		self.helper.layout = Layout(
			Row(button_args[0]),
			Row(HTML('&nbsp')),
			Row(button_args[1]),
			Row(HTML('&nbsp')),
			Row(button_args[2]),
		)
		
@access_validation()
def ParticipantWaiverChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	
	if request.method == 'POST':
		if 'ok-submit' in request.POST:
			participant.sign_waiver_now()
		elif 'not-ok-submit' in request.POST:
			participant.unsign_waiver_now()
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantWaiverForm()
		
	return render( request, 'participant_waiver_change.html', locals() )

#-----------------------------------------------------------------------

@autostrip
class ParticipantTagForm( Form ):
	tag = forms.CharField( required = False, label = _('Tag') )
	make_this_existing_tag = forms.BooleanField( required = False, label = _('Rider keeps tag for other races') )
	rfid_antenna = forms.ChoiceField( choices = ((0,_('None')), (1,'1'), (2,'2'), (3,'3'), (4,'4') ), label = _('RFID Antenna to Write Tag') )
	
	def __init__(self, *args, **kwargs):
		super(ParticipantTagForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'ok-submit', _('Update Tag in Database'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			Submit( 'auto-generate-tag-submit', _('Auto Generate Tag Only - Do Not Write'), css_class = 'btn btn-primary' ),
			Submit( 'write-tag-submit', _('Write Existing Tag'), css_class = 'btn btn-primary' ),
			Submit( 'auto-generate-and-write-tag-submit', _('Auto Generate and Write Tag'), css_class='btn btn-success' ),
		]
		
		self.helper.layout = Layout(
			Row(
				Col( Field('tag', rows='2', cols='60'), 4 ),
				Col( Field('make_this_existing_tag'), 4 ),
				Col( Field('rfid_antenna'), 4 ),
			),
			HTML( '<br/>' ),
			Row(
				button_args[4],
				HTML( '&nbsp;' * 5 ),
				button_args[3],
			),
			HTML( '<br/>' * 2 ),
			Row(
				button_args[2],
			),
			HTML( '<br/>' * 2 ),
			Row( 
				button_args[0],
				HTML( '&nbsp;' * 5 ),
				button_args[1],
			),
		)

@access_validation()
def ParticipantTagChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	competition = participant.competition
	license_holder = participant.license_holder
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = ParticipantTagForm( request.POST )
		if form.is_valid():
			status = True
			status_entries = []

			tag = form.cleaned_data['tag'].strip().upper()
			make_this_existing_tag = form.cleaned_data['make_this_existing_tag']
			rfid_antenna = request.session['rfid_antenna'] = int(form.cleaned_data['rfid_antenna'])
			
			if 'auto-generate-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				tag = license_holder.get_unique_tag()
				
			if not tag:
				status = False
				status_entries.append(
					(_('Empty Tag'), (
						_('Cannot write an empty Tag to the Database.'),
						_('Please specify a Tag or press Cancel.'),
					)),
				)
			elif not utils.allHex(tag):
				status = False
				status_entries.append(
					(_('Non-Hex Characters in Tag'), (
						_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
						_('Please change the Tag to all hexadecimal.'),
					)),
				)
			if not status:
				return render( request, 'rfid_write_status.html', locals() )
			
			participant.tag = tag
			try:
				participant.auto_confirm().save()
			except IntegrityError as e:
				# Report the error - probably a non-unique field.
				has_error, conflict_explanation, conflict_participant = participant.explain_integrity_error()
				status = False
				status_entries.append(
					(_('Participant Save Failure'), (
						u'{}'.format(e),
					)),
				)
				return render( request, 'rfid_write_status.html', locals() )
			
			if make_this_existing_tag:
				license_holder.existing_tag = tag
				try:
					license_holder.save()
				except Exception as e:
					# Report the error - probably a non-unique field.
					status = False
					status_entries.append(
						(string_concat(_('LicenseHolder'), u': ', _('Existing Tag Save Exception:')), (
							unicode(e),
						)),
					)
					return render( request, 'rfid_write_status.html', locals() )
			
			if 'write-tag-submit' in request.POST or 'auto-generate-and-write-tag-submit' in request.POST:
				if not rfid_antenna:
					status = False
					status_entries.append(
						(_('RFID Antenna Configuration'), (
							_('RFID Antenna for Tag Write must be specified.'),
							_('Please specify the RFID Antenna.'),
						)),
					)
				
				if status:
					status, response = WriteTag(tag, rfid_antenna)
					if not status:
						status_entries = [
							(_('Tag Write Failure'), response.get('errors',[]) ),
						]
				
				if not status:
					return render( request, 'rfid_write_status.html', locals() )
				# if status: fall through to ok-submit case.
			
			# ok-submit
			if 'auto-generate-tag-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'path'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantTagForm( initial = dict(tag=participant.tag, rfid_antenna=rfid_antenna, make_this_existing_tag=competition.use_existing_tags) )
		
	return render( request, 'participant_tag_change.html', locals() )
	
#-----------------------------------------------------------------------

@autostrip
class ParticipantSignatureForm( Form ):
	signature = forms.CharField( required = False, label = _('Signature') )
	
	def __init__(self, *args, **kwargs):
		is_jsignature = kwargs.pop( 'is_jsignature', True )
		super(ParticipantSignatureForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_id = 'id_signature_form'
		self.helper.form_class = 'navbar-form navbar-left'
		
		if is_jsignature:
			button_args = [
				Submit( 'ok-submit', ('&nbsp;'*10) + unicode(_('OK')) + ('&nbsp;'*10), css_class = 'btn btn-success', style='font-size:200%' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning hidden-print', style='font-size:200%' ),
				HTML(u'<button class="btn btn-warning hidden-print" onClick="reset_signature()">{}</button>'.format(_('Reset'))),
			]
		else:
			button_args = [
				HTML('&nbsp;'*24),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning hidden-print', style='font-size:150%' )
			]
		
		if is_jsignature:
			self.helper.layout = Layout(
				Container(
					Row( Col(Field('signature'), 12) ),
					Row( Col(Div(id="id_signature_canvas"), 12) ),

					Row(
						Col(button_args[0],4),
						Col(button_args[1],4),
						Col(button_args[2],4),
					),
				)
			)
		else:
			self.helper.layout = Layout(
				Container(
					Row( Col( Field( 'signature' ), 12) ),
					Row( Div( Div(*button_args, css_class='row'), css_class='col-md-12 text-center' ) ),
				)
			)

@access_validation()
def ParticipantSignatureChange( request, participantId ):
	participant = get_object_or_404( Participant, pk=participantId )
	signature_with_touch_screen = int(request.session.get('signature_with_touch_screen', True))
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = ParticipantSignatureForm( request.POST, is_jsignature=signature_with_touch_screen )
		if form.is_valid():
			signature = form.cleaned_data['signature']
			signature = signature.strip()
			if not signature:
				return HttpResponseRedirect(getContext(request,'path'))
				
			participant.signature = signature
			participant.auto_confirm().save()
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = ParticipantSignatureForm( is_jsignature=signature_with_touch_screen )
	
	if signature_with_touch_screen:
		return render( request, 'participant_jsignature_change.html', locals() )
	else:
		return render( request, 'participant_signature_change.html', locals() )
	
@access_validation()
def SetSignatureWithTouchScreen( request, use_touch_screen ):
	request.session['signature_with_touch_screen'] = bool(int(use_touch_screen))
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------

@access_validation()
def ParticipantBarcodeAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	add_by_barcode = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = BarcodeScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
			scan = form.cleaned_data['scan'].strip()
			if not scan:
				return HttpResponseRedirect(getContext(request,'path'))
				
			license_holder, participants = participant_key_filter( competition, scan, False )
			license_holders = []	# Required for participant_scan_error.
			if not license_holder:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(participants) == 1:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			if len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holder.id))
	else:
		form = BarcodeScanForm( hide_cancel_button=True )
		
	return render( request, 'participant_scan_form.html', locals() )
	
@access_validation()
def ParticipantNotFound( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_not_found.html', locals() )
	
@access_validation()
def ParticipantMultiFound( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	return render( request, 'participant_multi_found.html', locals() )
	
#-----------------------------------------------------------------------

@access_validation()
def ParticipantRfidAdd( request, competitionId, autoSubmit=False ):
	competition = get_object_or_404( Competition, pk=competitionId )
	rfid_antenna = int(request.session.get('rfid_antenna', 0))
	
	status = True
	status_entries = []
	tag = None
	tags = []
	
	add_by_rfid = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = RfidScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
		
			request.session['rfid_antenna'] = rfid_antenna = int(form.cleaned_data['rfid_antenna'])
			
			if not rfid_antenna:
				status = False
				status_entries.append(
					(_('RFID Antenna Configuration'), (
						_('RFID Antenna for Tag Read must be specified.'),
						_('Please specify the RFID Antenna.'),
					)),
				)
			else:
				status, response = ReadTag(rfid_antenna)
				# DEBUG DEBUG
				#status, response = True, {'tags': ['A7A2102303']}
				if not status:
					status_entries.append(
						(_('Tag Read Failure'), response.get('errors',[]) ),
					)
				else:
					tags = response.get('tags', [])
					try:
						tag = tags[0]
					except (AttributeError, IndexError) as e:
						status = False
						status_entries.append(
							(_('Tag Read Failure'), [e] ),
						)
				
				if tag and len(tags) > 1:
					status = False
					status_entries.append(
						(_('Multiple Tags Read'), tags ),
					)
			
			if not status:
				return render( request, 'participant_scan_rfid.html', locals() )
				
			license_holder, participants = participant_key_filter( competition, tag, False )
			license_holders = []	# Required for participant_scan_error.
			if not license_holder:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(participants) == 1:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			if len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holder.id))
	else:
		form = RfidScanForm( initial=dict(rfid_antenna=rfid_antenna), hide_cancel_button=True )
		
	return render( request, 'participant_scan_rfid.html', locals() )

@access_validation()
def LicenseHolderAddConfirm( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	competition_age = competition.competition_age( license_holder )
	return render( request, 'license_holder_add_confirm.html', locals() )

@access_validation()
def LicenseHolderConfirmAddToCompetition( request, competitionId, licenseHolderId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	
	# Try to create a new participant from the license_holder.
	participant = Participant( competition=competition, license_holder=license_holder, preregistered=False ).init_default_values()
	try:
		participant.auto_confirm().save()
		participant.add_to_default_optional_events()
		return HttpResponseRedirect(pushUrl(request, 'ParticipantEdit', participant.id, cancelUrl=True))
	except IntegrityError as e:
		# If this participant exists already, recover silently by going directly to the existing participant.
		participant = Participant.objects.filter(competition=competition, license_holder=license_holder).first()
		return HttpResponseRedirect(pushUrl(request, 'ParticipantEdit', participant.id, cancelUrl=True))

#-----------------------------------------------------------------------
@autostrip
class BibScanForm( Form ):
	bib = forms.IntegerField( required = False, label = _('Bib') )
	
	def __init__(self, *args, **kwargs):
		hide_cancel_button = kwargs.pop('hide_cancel_button', None)
		super(BibScanForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'navbar-form navbar-left'
		
		button_args = [
			Submit( 'search-submit', _('Search'), css_class = 'btn btn-primary' ),
			Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
		]
		if hide_cancel_button:
			button_args = button_args[:-1]
		
		self.helper.layout = Layout(
			Row(
				Field('bib', size=10),
			),
			Row( *button_args ),
		)

@access_validation()
def ParticipantBibAdd( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	add_by_bib = True
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = BibScanForm( request.POST, hide_cancel_button=True )
		if form.is_valid():
			bib = form.cleaned_data['bib']
			if not bib:
				return HttpResponseRedirect(getContext(request,'path'))
				
			license_holders, participants = participant_bib_filter( competition, bib )
			if len(participants) == 1:
				return HttpResponseRedirect(pushUrl(request,'ParticipantEdit',participants[0].id))
			elif len(participants) > 1:
				return render( request, 'participant_scan_error.html', locals() )
			
			if len(license_holders) == 1:
				return HttpResponseRedirect(pushUrl(request,'LicenseHolderAddConfirm', competition.id, license_holders[0].id))
			return render( request, 'participant_scan_error.html', locals() )			
	else:
		form = BibScanForm( hide_cancel_button=True )
	
	return render( request, 'participant_add_bib.html', locals() )
	
#-----------------------------------------------------------------------

@autostrip
class SystemInfoForm( ModelForm ):
	class Meta:
		model = SystemInfo
		fields = '__all__'
		
	def __init__( self, *args, **kwargs ):
		button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
		super(SystemInfoForm, self).__init__(*args, **kwargs)
		
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(
				Col(Field('tag_template', size=24), 6),
			),
			HTML( '<hr/>' ),
			Row(
				Col(Field('print_tag_option'), 4),
				Col(Field('server_print_tag_cmd', size=80), 8),				
			),
			HTML( '<hr/>' ),
			Row(
				Col(Field('tag_from_license'), 4),
				Col(Field('tag_from_license_id'), 4),
			),
			HTML( '<hr/>' ),
			Row(
				Col(Field('reg_closure_minutes', size=6), 6),
			),
			Row(
				Col(Field('exclude_empty_categories', size=6), 6),
			),
			Row(
				Col(Field('reg_allow_add_multiple_categories', size=6), 6),
			),
			Row(
				Col(Field('license_code_regex', size=80), 6),
			),
			Row(
				Col(Field('cloud_server_url', size=80), 6),
			),
			HTML( '<hr/>' ),
			Field( 'rfid_server_host', type='hidden' ),
			Field( 'rfid_server_port', type='hidden' ),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SystemInfoEdit( request ):
	return GenericEdit( SystemInfo, request, SystemInfo.get_singleton().id, SystemInfoForm )
	
#-----------------------------------------------------------------------

def get_year_choices():
	year_choices = [
		(y, u'{}'.format(y))
			for y in sorted(
			set(d.year for d in Competition.objects.all()
				.order_by('-start_date')
				.values_list('start_date', flat=True)), reverse=True
			)
	][:20] + [(-1, _('All'))]
	return year_choices
	
def get_search_start_date():
	last_competition = Competition.objects.all().order_by('-start_date').first()
	return datetime.date( last_competition.start_date.year, 1, 1 ) if last_competition else None
	
def get_search_end_date():
	last_competition = Competition.objects.all().order_by('-start_date').first()
	return datetime.date( last_competition.start_date.year, 12, 31 ) if last_competition else None
	
def get_organizer_choices():
	return [(v, v) for v in sorted( set(Competition.objects.all().values_list('organizer', flat=True) ) )]

def get_discipline_choices():
	return [(id, name) for seq, id, name in sorted( set(Competition.objects.all().values_list(
		'discipline__sequence','discipline__id', 'discipline__name')
	) )]

def get_race_class_choices():
	return [(id, name) for seq, id, name in sorted( set(Competition.objects.all().values_list(
		'race_class__sequence','race_class__id', 'race_class__name')
	) )]

def get_participant_report_form():
	@autostrip
	class ParticipantReportForm( Form ):
		start_date = forms.DateField( required = False, label = _('Start Date') )
		end_date = forms.DateField( required = False, label = _('End Date')  )
		race_classes = forms.MultipleChoiceField( required = False, label = _('Race Classes'), choices = get_race_class_choices() )
		disciplines = forms.MultipleChoiceField( required = False, label = _('Disciplines'), choices = get_discipline_choices() )
		organizers = forms.MultipleChoiceField( required = False, label = _('Organizers'), choices = get_organizer_choices() )
		include_labels = forms.MultipleChoiceField( required = False, label = _('Include Labels'), choices = [(r.pk, r.name) for r in ReportLabel.objects.all()] )
		exclude_labels = forms.MultipleChoiceField( required = False, label = _('Exclude Labels'), choices = [(r.pk, r.name) for r in ReportLabel.objects.all()] )
		
		def __init__( self, *args, **kwargs ):
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			super(ParticipantReportForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.additional_buttons = []
			if button_mask == EDIT_BUTTONS:
				self.additional_buttons.append( ('emails-submit', _('Emails'), 'btn btn-primary') )
				self.additional_buttons.append( ('excel-export-submit', _('Export LicenseHolders to Excel'), 'btn btn-primary') )
			
			self.helper.layout = Layout(
				Row(
					Div(
						Row( Field('start_date') ),
						Row( Field('end_date') ),
						css_class = 'col-md-3'
					),
					Div(
						Row(
							Field('race_classes', id='focus', size=10),
							Field('disciplines', size=10),
							Field('organizers', size=10),
							Field('include_labels', size=10),
							Field('exclude_labels', size=10),
						),
						Row( HTML( _('Use Ctrl-Click to Multi-Select and Ctrl-Click to Deselect') ) ),
						css_class = 'col-md-9',
					)
				),
				HTML( '<hr/>' ),
			)
			addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, additional_buttons=self.additional_buttons )
	
		def clean(self):
			cleaned_data = super(ParticipantReportForm, self).clean()
			start_date = cleaned_data.get("start_date")
			end_date = cleaned_data.get("end_date")

			if start_date and end_date:
				if start_date > end_date:
					raise forms.ValidationError( _("Start Date must be less than End Date") )
			return cleaned_data
	
	return ParticipantReportForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def ParticipantReport( request ):
	start_date, end_date, discipline, race_classes = get_search_start_date(), get_search_end_date(), None, None
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = get_participant_report_form()( request.POST )
		start_date, end_date, discipline, race_classes = None, None, None, None
		if form.is_valid():
			start_date = form.cleaned_data['start_date']
			end_date = form.cleaned_data['end_date']
			disciplines = form.cleaned_data['disciplines']
			race_classes = form.cleaned_data['race_classes']
			organizers = form.cleaned_data['organizers']
			include_labels = form.cleaned_data['include_labels']
			exclude_labels = form.cleaned_data['exclude_labels']
			
		sheet_name, xl = participation_excel( start_date, end_date, disciplines, race_classes, organizers, include_labels, exclude_labels )
		response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
		response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(sheet_name)
		return response
	else:
		form = get_participant_report_form()( initial={'start_date':start_date, 'end_date':end_date} )
		
	return render( request, 'generic_form.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def AttendanceAnalytics( request ):
	initial = request.session.get( 'attendance_analytics', {
			'start_date':get_search_start_date(),
			'end_date':get_search_end_date(),
			'disciplines':[],
			'race_classes':[],
			'organizers':[],
		}
	)
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
		form = get_participant_report_form()( request.POST )
		if form.is_valid():
			initial = {
				k:form.cleaned_data[k] for k in (
					'start_date',
					'end_date',
					'disciplines',
					'race_classes',
					'organizers',
					'include_labels',
					'exclude_labels',
				)
			}
			
			if 'emails-submit' in request.POST:
				return show_emails(
					request,
					emails=itertools.chain.from_iterable(
						c.get_participants().exclude(license_holder__email='').values_list('license_holder__email',flat=True)
							for c in get_competitions(**initial)
					)
				)
		
			if 'excel-export-submit' in request.POST:
				q = Q( pk__in = set(itertools.chain.from_iterable(
						c.get_participants().values_list('license_holder__pk',flat=True) for c in get_competitions(**initial)
					))
				)
				xl = get_license_holder_excel( q )
				response = HttpResponse(xl, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
				response['Content-Disposition'] = 'attachment; filename=RaceDB-Analytics-LicenseHolders-{}.xlsx'.format(
					datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
				)
				return response
		
			payload, license_holders_event_errors = participation_data( **initial )
			payload_json = json.dumps(payload, separators=(',',':'))
	else:
		payload, license_holders_event_errors = participation_data( **initial )
		payload_json = json.dumps(payload, separators=(',',':'))
		form = get_participant_report_form()( initial=initial )
	
	page_title = [u'Analytics']
	if initial.get('start_date',None) is not None:
		page_title.append( u'from {}'.format( initial['start_date'] .strftime('%Y-%m-%d') ) )
	if initial.get('end_date', None) is not None:
		page_title.append( u'to {}'.format( initial['end_date'].strftime('%Y-%m-%d') ) )
	if initial.get('organizers',None):
		page_title.append( u'for {}'.format( u', '.join(initial['organizers']) ) )
	page_title = u' '.join( page_title )
		
	def get_name( cls, id ):
		obj = cls.objects.filter(id=id).first()
		return obj.name if obj else ''
	
	if initial.get('disciplines',None):
		page_title += u' ({})'.format( u','.join( d.name for d in Discipline.objects.filter(pk__in=initial['disciplines'])) )
	if initial.get('race_classes',None):
		page_title += u' ({})'.format(u','.join( d.name for d in RaceClass.objects.filter(pk__in=initial['race_classes'])) )
	if initial.get('include_labels', None):
		page_title += u', +({})'.format( u','.join( r.name for r in ReportLabel.objects.filter(pk__in=initial['include_labels'])) )
	if initial.get('exclude_labels',None):
		page_title += u', -({})'.format( u','.join( r.name for r in ReportLabel.objects.filter(pk__in=initial['exclude_labels'])) )
		
	return render( request, 'system_analytics.html', locals() )
	
#-----------------------------------------------------------------------

def get_discipline_race_class_choices():
	discipline_used, race_class_used = set(), set()
	for competition in Competition.objects.all():
		discipline_used.add( competition.discipline )
		race_class_used.add( competition.race_class )
	discipline_choices = [(0,_('All'))] + [(d.id, d.name) for d in sorted(discipline_used, key=lambda x: x.sequence)]
	race_class_choices = [(0,_('All'))] + [(d.id, d.name) for d in sorted(race_class_used, key=lambda x: x.sequence)]
	return discipline_choices, race_class_choices

def get_year_on_year_form():
	@autostrip
	class YearOnYearReportForm( Form ):
		discipline_choices, race_class_choices = get_discipline_race_class_choices()
		discipline = forms.ChoiceField( required = False, label = _('Discipline'), choices = discipline_choices )
		race_class = forms.ChoiceField( required = False, label = _('Race Class'), choices = race_class_choices )
		organizers = forms.MultipleChoiceField( required = False, label = _('Organizers'), choices = get_organizer_choices(), help_text=_('Ctrl-Click to Multi-Select') )
		include_labels = forms.MultipleChoiceField( required = False, label = _('Include Labels'), choices = [(r.pk, r.name) for r in ReportLabel.objects.all()], help_text=_('Ctrl-Click to Multi-Select') )
		exclude_labels = forms.MultipleChoiceField( required = False, label = _('Exclude Labels'), choices = [(r.pk, r.name) for r in ReportLabel.objects.all()], help_text=_('Ctrl-Click to Multi-Select') )
		
		def __init__( self, *args, **kwargs ):
			super(YearOnYearReportForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.helper.layout = Layout(
				Row(
					Field('discipline', id='focus'), Field('race_class'),
					Field('organizers', size=8),
					Field('include_labels', size=8),
					Field('exclude_labels', size=8),
				),
				HTML( '<hr/>' ),
			)
			addFormButtons( self, OK_BUTTON | CANCEL_BUTTON )
	
	return YearOnYearReportForm

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def YearOnYearAnalytics( request ):
	initial = request.session.get( 'attendance_analytics', {
			'discipline':-1,
			'race_class':-1,
			'organizers':[],
		}
	)
	
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = get_year_on_year_form()( request.POST )
		if form.is_valid():
			initial = {
				'discipline':int(form.cleaned_data['discipline']),
				'race_class':int(form.cleaned_data['race_class']),
				'organizers':form.cleaned_data['organizers'],
				'include_labels':form.cleaned_data['include_labels'],
				'exclude_labels':form.cleaned_data['exclude_labels'],
			}
			
			payload = year_on_year_data( **initial )
			payload_json = json.dumps(payload, separators=(',',':'))
	else:
		payload = year_on_year_data( **initial )
		payload_json = json.dumps(payload, separators=(',',':'))
		form = get_year_on_year_form()( initial=initial )
	
	page_title = [u'Year on Year Analytics']
	if initial.get('organizers',None):
		page_title.append( u'for {}'.format( u', '.join(initial['organizers']) ) )
	page_title = u' '.join( page_title )
		
	def get_name( cls, id ):
		obj = cls.objects.filter(id=id).first()
		return obj.name if obj else ''
	
	if initial.get('discipline',0) > 0:
		page_title += u' {}'.format(get_name(Discipline, initial['discipline']))
	if initial.get('race_class',0) > 0:
		page_title += u' {}'.format(get_name(RaceClass, initial['race_class']))
	if initial.get('include_labels', None):
		page_title += u', +({})'.format( u','.join( r.name for r in ReportLabel.objects.filter(pk__in=initial['include_labels'])) )
	if initial.get('exclude_labels',None):
		page_title += u', -({})'.format( u','.join( r.name for r in ReportLabel.objects.filter(pk__in=initial['exclude_labels'])) )
		
	return render( request, 'year_on_year_analytics.html', locals() )

#-----------------------------------------------------------------------

def GetEvents( request, date=None ):
	if date is None:
		date = datetime.date.today()
	else:
		date = datetime.date( *[int(d) for d in date.split('-')] )
	
	events = list( EventMassStart.objects.filter(
		date_time__year = date.year, date_time__month = date.month, date_time__day = date.day,
	)) + list( EventTT.objects.filter(
		date_time__year = date.year, date_time__month = date.month, date_time__day = date.day,
	))
	events.sort( key=lambda e:e.date_time )
	response = {
		'date': date.strftime('%Y-%m-%d'),
		'events': [e.get_json() for e in events],
	}
	return JsonResponse( response )

#-----------------------------------------------------------------------

def QRCode( request ):
	exclude_breadcrumbs = True
	qrpath = request.build_absolute_uri()
	for i in xrange(2):
		qrpath = os.path.dirname( qrpath )
	qrpath += '/'
	return render( request, 'qrcode.html', locals() )
	
#-----------------------------------------------------------------------
from competition_import_export import competition_import, competition_export, get_competition_name_start_date
import tempfile
from wsgiref.util import FileWrapper
import json
import gzip
import shutil
import requests
from django.http import StreamingHttpResponse

@autostrip
class ExportCompetitionForm( Form ):
	export_as_template = forms.BooleanField( required=False, label=_('Export as Template (exclude Participants and Teams)') )
	remove_ftp_info = forms.BooleanField( required=False, label=_('Remove FTP Upload Info') )
	
	def __init__( self, *args, **kwargs ):
		super( ExportCompetitionForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		url = SystemInfo.get_singleton().cloud_server_url
		self.helper.layout = Layout(
			Row(Field('export_as_template')),
			Row(Field('remove_ftp_info')),
			Row(HTML('Cloud Server URL: <strong>' + url + '</strong>') if url else HTML(_('To Export to Cloud RaceDB, configure Cloud Server URL in SystemInfo')) )
		)
		
		self.additional_buttons = []
		if url:
			self.additional_buttons.append( ('ok-cloud-submit', _('Export to Cloud Server'), 'btn btn-primary'), )
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done'), additional_buttons=self.additional_buttons )

def get_compressed_competition_json( competition, export_as_template=False, remove_ftp_info=False ):
	# Create a temp file.
	gzip_stream = tempfile.TemporaryFile()
	# Create a gzip and connect it to the temp file.
	gzip_handler = gzip.GzipFile( fileobj=gzip_stream, mode="wb", filename='{}.json'.format(competition.get_filename_base()) )
	# Write the competition json to the gzip obj, which compresses it and writes it to the temp file.
	competition_export( competition, gzip_handler, export_as_template=export_as_template, remove_ftp_info=remove_ftp_info )
	# Make sure gzip flushes all its buffers.
	gzip_handler.flush()
	gzip_handler.close()	# Does not close underlying fileobj.
	return gzip_stream

def handle_export_competition( competition, export_as_template=False, remove_ftp_info=False ):
	gzip_stream = get_compressed_competition_json( competition, export_as_template=export_as_template, remove_ftp_info=remove_ftp_info )
		
	# Generate the response using the file wrapper, content type: x-gzip
	# Since this file can be big, best to use the StreamingHTTPResponse
	# that way we can guarantee that the file will be sent entirely.
	response = StreamingHttpResponse( gzip_stream, content_type='application/x-gzip' )

	# Content size
	gzip_stream.seek(0, 2)
	response['Content-Length'] = gzip_stream.tell()
	gzip_stream.seek( 0 )

	# Add content disposition so the browser will download the file.
	response['Content-Disposition'] = 'attachment; filename={}.gzip'.format(competition.get_filename_base())

	# Send back the response to the request.
	return response	

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionExport( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	title = string_concat( _('Export'), u': ', competition.name )
	
	response = {}
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = ExportCompetitionForm(request.POST)
		if form.is_valid():
			url = SystemInfo.get_singleton().cloud_server_url
			
			i = url.find( 'RaceDB' )
			if i > 0:
				url = url[:i+len('RaceDB')]
				
			if not url.endswith('/'):
				url += '/'
			if 'CompetitionCloudUpload' not in url:
				url += 'CompetitionCloudUpload/'

			if 'ok-cloud-submit' in request.POST:
				gzip_stream = get_compressed_competition_json(
					competition,
					form.cleaned_data['export_as_template'],
					form.cleaned_data['remove_ftp_info'],
				)
				gzip_stream.seek(0, 2)
				headers = {
					'Content-Length': gzip_stream.tell(),
					'Content-Type': 'application/octet-stream',
				}
				gzip_stream.seek(0, 0)
				response = requests.post(url, data=gzip_stream, headers=headers)
			else:
				return handle_export_competition(
					competition,
					form.cleaned_data['export_as_template'],
					form.cleaned_data['remove_ftp_info'],
				)
	else:
		form = ExportCompetitionForm()
	
	return render( request, 'export_competition.html', locals() )
	
@autostrip
class ImportCompetitionForm( Form ):
	json_file = forms.FileField( required=True, label=_('Competition File (*.gzip|*.json)') )
	
	name = forms.CharField( required=False, label=_('Change Name to'), help_text=_('Leave blank to use Competition name in import file') )
	start_date = forms.DateField( required=False, label=_('Change Start Date to'), help_text=_('Leave blank to use Competition date in import file') )
	import_as_template = forms.BooleanField( required=False, label=_('Import as Template (ignore Participants and Teams)') )
	
	def __init__( self, *args, **kwargs ):
		super( ImportCompetitionForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(Field('json_file', accept=".gzip,.gz,.json")),
			Row(HTML('&nbsp;')),
			Row(Col(Field('name'), 6), Col(Field('start_date'), 3)),
			Row(Field('import_as_template')),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_import_competition( json_file_request, import_as_template=False, name=None, start_date=None, replace=False ):
	try:
		if json_file_request.name.endswith('.gzip') or json_file_request.name.endswith('.gz'):
			json_file_request = gzip.GzipFile(filename=json_file_request.name, fileobj=json_file_request, mode='rb')
	except Exception as e:
		pass
		
	message_stream = StringIO.StringIO()
		
	try:
		name, start_date, pydata = get_competition_name_start_date(
			stream=json_file_request,
			import_as_template=import_as_template,
			name=name,
			start_date=start_date,
		 )
		if name is None:
			message_stream.write( 'Error: Missing Competition Name and Start Date.\n' )
			return message_stream.getvalue()
		
	except Exception as e:
		message_stream.write( 'Error: Cannot find Competition Name and Start Date.\n' )
		message_stream.write( 'Error: "{}".\n'.format(e) )
		return message_stream.getvalue()
			
	if replace:
		Competition.objects.filter( name=name, start_date=start_date ).delete()
	elif Competition.objects.filter( name=name, start_date=start_date ).exists():
		message_stream.write( 'Error: Competition "{}" "{}" exists already.\n'.format(name, start_date.strftime('%Y-%m-%d')) )
		message_stream.write( 'Rename or Delete the existing Competition before importing.' )
		return message_stream.getvalue()

	competition_import( pydata=pydata )
	message_stream.write( 'Competition "{}" "{}" imported.\n'.format(name, start_date.strftime('%Y-%m-%d')) )
	message_stream.write( 'Success!\n' )
	
	return message_stream.getvalue()

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionImport( request ):
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = ImportCompetitionForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_import_competition(
				request.FILES['json_file'],
				form.cleaned_data['import_as_template'],
				form.cleaned_data['name'] or None,
				form.cleaned_data['start_date'] or None,
			)
			return render( request, 'import_competition.html', locals() )
	else:
		form = ImportCompetitionForm()
	
	return render( request, 'import_competition.html', locals() )
	
@csrf_exempt
def CompetitionCloudUpload( request ):
	print 'CompetitionCloudUpload: processing...'
	response = {'errors':[], 'warnings':[], 'message':''}
	if request.method == "POST":
		try:
			gzip_handler = gzip.GzipFile(fileobj=StringIO.StringIO(request.body), mode='rb')
			response['message'] = handle_import_competition( gzip_handler, import_as_template=False, replace=True )
		except Exception as e:
			response['errors'].append( 'Competition Upload Error: {}'.format(e) )
	else:
		response['errors'].append( u'Request must be of type POST with gzip json payload.' )
	print 'CompetitionCloudUpload: done.'
	print response['message']
	for e in response['errors']:
		print 'Error:', e
	for w in response['warnings']:
		print 'Error:', w
	return JsonResponse( response )

#-----------------------------------------------------------------------

def Logout( request ):
	return logout( request, next_page=getContext(request, 'cancelUrl') )
