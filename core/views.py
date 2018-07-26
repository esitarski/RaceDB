from views_common import *
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.html import escape
from django.contrib.auth.views import logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden

import zipfile
import operator
import itertools
import traceback

from get_crossmgr_excel import get_crossmgr_excel, get_crossmgr_excel_tt
from get_seasons_pass_excel import get_seasons_pass_excel
from get_number_set_excel import get_number_set_excel
from get_start_list_excel import get_start_list_excel
from get_license_holder_excel import get_license_holder_excel
from participation_excel import participation_excel
from participation_data import participation_data, get_competitions
from year_on_year_data import year_on_year_data
from license_holder_import_excel import license_holder_import_excel, license_holder_msg_to_html
from uci_excel_dataride import uci_excel
import authorization

from participant_key_filter import participant_key_filter, participant_bib_filter
from init_prereg import init_prereg
from emails import show_emails

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
			Submit( 'check-tag-submit', _('Check Tag'), css_class = 'btn btn-primary' ),
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
	system_info = SystemInfo.get_singleton()
	
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
			if any(submit_btn in request.POST for submit_btn in ('check-tag-submit','write-tag-submit','auto-generate-and-write-tag-submit') ):
			
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
				elif system_info.tag_all_hex and not utils.allHex(tag):
					status = False
					status_entries.append(
						(_('Non-Hex Characters in Tag'), (
							_('All Tag characters must be hexadecimal ("0123456789ABCDEF").'),
							_('Please change the Tag to all hexadecimal.'),
						)),
					)
				
				if status:
					if 'check-tag-submit' in request.POST:
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
				Col(Field('city', size=32), 3),
				Col(Field('state_prov', size=20), 3),
				Col(Field('nationality', size=18), 2),
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
					Field('uci_id', maxlength=24),
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
				Col(Field('existing_tag', size=30), 4),
				Col(Field('existing_tag2', size=30), 4),
				Col(Field('active'), 4),
			),
			Row(
				ColKey(
					HTML(warning_html(lh and not lh.emergency_contact_name)),
					Field('emergency_contact_name', size=50),
					cols=5,
				),
				ColKey(
					HTML(warning_html(lh and not lh.emergency_contact_phone)),
					Field('emergency_contact_phone'),
					cols=3,
				),
				Col(Field('emergency_medical', size=30), 3),
			),
			Row(
				Col('eligible', 2),
				Col( HTML(_('If not Eligible to Compete, this License Holder will not be allowed to participate in races until it is reset.  Always add a note (below) explaining the reason.')), 6 ),
			),
			Row(
				Field('note', cols=80, rows=1),
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
	
	if not license_holders and search_text.startswith( 'rfid=' ):
		arg = search_text.split('=',1)[1].strip().upper().lstrip('0')
		license_holders = list(LicenseHolder.objects.filter(Q(existing_tag=arg) | Q(existing_tag2=arg)))
		
	if not license_holders and search_text.startswith( 'scan=' ):
		arg = search_text.split('=',1)[1].strip().upper().lstrip('0').replace(u' ', u'')
		license_holders = list(LicenseHolder.objects.filter( Q(license_code=arg) | Q(uci_id=arg) ))

	if not license_holders and is_uci_id( search_text ):
		license_holders = list(LicenseHolder.objects.filter(uci_id = search_text.replace(' ','')))
	
	if not license_holders and reUCICode.match( search_text ):
		license_holders = list(LicenseHolder.objects.filter(uci_code = search_text.upper()))
			
	if not license_holders and search_text[-4:].isdigit():
		license_holders = list(LicenseHolder.objects.filter(license_code = search_text.upper().lstrip('0')))

	if not license_holders:
		if search_text:
			q = Q()
			for n in search_text.split():
				q &= Q( search_text__contains = n )
			license_holders = LicenseHolder.objects.filter(q)[:MaxReturn]
		else:
			license_holders = LicenseHolder.objects.all()[:MaxReturn]
	
	return license_holders
	
@access_validation()
def LicenseHoldersDisplay( request ):

	search_text = request.session.get('license_holder_filter', '')
	btns = [
		('search-by-barcode-submit', _('Barcode/License/UCIID/Tag Search'), 'btn btn-primary', True),
		('search-by-tag-submit', _('RFID Search'), 'btn btn-primary', True),
		('clear-search-submit', _('Clear Search'), 'btn btn-primary', True),
		('new-submit', _('New LicenseHolder'), 'btn btn-success'),
		('correct-errors-submit', _('Correct Errors'), 'btn btn-primary'),
		('manage-duplicates-submit', _('Manage Duplicates'), 'btn btn-primary'),
		('auto-create-tags-submit', _('Auto Create All Tags'), 'btn btn-primary'),
		('reset-existing-bibs-submit', _('Reset Existing Bib Numbers'), 'btn btn-primary'),
		('export-excel-submit', _('Export to Excel'), 'btn btn-primary'),
		('import-excel-submit', _('Import from Excel'), 'btn btn-primary'),
	]

	if SystemInfo.get_singleton().cloud_server_url:
		btns.append(
		('cloud-import-submit', _('Cloud Import'), 'btn btn-primary'),
		)
	
	if request.method == 'POST':
	
		if 'clear-search-submit' in request.POST:
			request.session['license_holder_filter'] = ''
			return HttpResponseRedirect( '.' )

		for submit_btn, action in (
				('cancel-submit',				lambda: HttpResponseRedirect( getContext(request,'cancelUrl')) ),
				('search-by-barcode-submit',	lambda: HttpResponseRedirect( pushUrl(request,'LicenseHolderBarcodeScan') )),
				('search-by-tag-submit', 		lambda: HttpResponseRedirect( pushUrl(request,'LicenseHolderRfidScan') )),
				('new-submit',					lambda: HttpResponseRedirect( pushUrl(request,'LicenseHolderNew') )),
				('correct-errors-submit',		lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersCorrectErrors') )),
				('manage-duplicates-submit',	lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersManageDuplicates') )),
				('auto-create-tags-submit',		lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersAutoCreateTags') )),
				('reset-existing-bibs-submit',	lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersResetExistingBibs') )),
				('import-excel-submit',			lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersImportExcel') )),
				('cloud-import-submit',			lambda: HttpResponseRedirect( pushUrl(request,'LicenseHoldersCloudImport') )),
			):
			if submit_btn in request.POST:
				return action()
		
		form = SearchForm( btns, request.POST, additional_buttons_on_new_row=True )
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
		form = SearchForm( btns, initial = {'search_text': search_text}, additional_buttons_on_new_row=True )
	
	license_holders = license_holders_from_search_text( search_text )
	isEdit = True
	return render( request, 'license_holder_list.html', locals() )

#--------------------------------------------------------------------------
@autostrip
class BarcodeScanForm( Form ):
	scan = forms.CharField( required = False, label = _('Barcode (License Code, RFID Tag or UCIID)') )
	
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
			Row( *(button_args + [HTML('&nbsp;'*12), Field('rfid_antenna')]) ),
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
	message = [_("Create tag values for all License Holders.")]
	message.append( '    ' )
	system_info = SystemInfo.get_singleton()
	if system_info.tag_creation == 0:
		message.append(_('Existing tags will not work anymore.'))
	elif system_info.tag_creation == 1:
		message.append(_('Existing tags *may* not work anymore.'))
	else:
		message.append(_('Existing tags will work if the License Codes have not changed.'))
	message = string_concat( *message )
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'LicenseHoldersAutoCreateTags/1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def LicenseHoldersManageDuplicates( request ):
	duplicates = LicenseHolder.get_duplicates()
	return render( request, 'license_holder_duplicate_list.html', locals() )

def format_uci_id( uci_id ):
	uci_id = uci_id or u''
	return u' '.join( uci_id[i:i+3] for i in xrange(0, len(uci_id), 3) )

def GetLicenseHolderSelectDuplicatesForm( duplicates ):
	
	choices = [(lh.pk, u'{last_name}, {first_name} - {gender} - {date_of_birth} - {city}, {state_prov} - {nation_code} - {license} - {uci_id} - ({num_comps})'.format(
		last_name=lh.last_name,
		first_name=lh.first_name,
		gender=lh.get_gender_display(),
		date_of_birth=lh.date_of_birth,
		state_prov=lh.state_prov,
		city=lh.city,
		nation_code=lh.nation_code,
		uci_id=format_uci_id( lh.uci_id ),
		license=lh.license_code_trunc,
		num_comps=Participant.objects.filter( license_holder=lh ).count(),
	)) for lh in duplicates]
	
	@autostrip
	class LicenseHolderSelectDuplicatesForm( Form ):
		pks = forms.MultipleChoiceField(
			required = False, label = _('Confirm Potential Duplicates'),
			choices=choices, widget=forms.CheckboxSelectMultiple
		)
		
		def __init__(self, *args, **kwargs):
			super(LicenseHolderSelectDuplicatesForm, self).__init__(*args, **kwargs)
			
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = ''
			
			button_args = [
				Submit( 'ok-submit', _('OK'), css_class = 'btn btn-primary' ),
				Submit( 'cancel-submit', _('Cancel'), css_class = 'btn btn-warning' ),
			]
			
			self.helper.layout = Layout(
				Row(
					HTML('<div class="well">'), Field('pks'), HTML('</div>'),
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
def LicenseHoldersResetExistingBibs( request, confirmed=False ):
	if confirmed:
		LicenseHolder.objects.exclude(existing_bib__isnull=True).update( existing_bib=None )
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
		
	page_title = _('Reset Exsting Bibs')
	message = _('This will reset all existing bibs to null (no value).')
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'popUrl') + 'LicenseHoldersResetExistingBibs/1/'
	return render( request, 'are_you_sure.html', locals() )

#-----------------------------------------------------------------------
@access_validation()
def LicenseHolderNew( request ):
	return GenericNew( LicenseHolder, request, LicenseHolderForm,
		instance_fields={'license_code': 'TEMP'}
	)
	
@access_validation()
def LicenseHolderEdit( request, licenseHolderId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	return GenericEdit( LicenseHolder, request,
		licenseHolderId,
		LicenseHolderForm,
		template='license_holder_form.html',
		additional_context={'discipline_team':[(d, license_holder.get_team_for_discipline(d)) for d in Discipline.get_disciplines_in_use()],},
	)
	
@access_validation()
def LicenseHolderDelete( request, licenseHolderId ):
	return GenericDelete( LicenseHolder, request,
		licenseHolderId,
		LicenseHolderForm,
		template='license_holder_form.html',
	)
		
@access_validation()
def LicenseHolderTeamChange( request, licenseHolderId, disciplineId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	discipline = get_object_or_404( Discipline, pk=disciplineId ) if int(disciplineId) else None
	team = license_holder.get_team_for_discipline(discipline) if discipline else None
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
	return render( request, 'license_holder_team_select.html', locals() )

def LicenseHolderTeamSelect( request, licenseHolderId, disciplineId, teamId ):
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	discipline = get_object_or_404( Discipline, pk=disciplineId ) if int(disciplineId) else None
	team = get_object_or_404( Team, pk=teamId ) if int(teamId) else None
	if not discipline:
		TeamHint.set_all_disciplines( license_holder, team )
	else:
		TeamHint.set_discipline( license_holder, discipline, team )
	return HttpResponseRedirect(getContext(request,'pop2Url'))
	
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
			superuser_btns = []
			superuser_btns.append( Submit('new-submit', _('New Competition'), css_class = 'btn btn-success') )
			if SystemInfo.get_singleton().cloud_server_url:
				superuser_btns.append( Submit('import-cloud-submit', _('Import Competitions from Cloud'), css_class = 'btn btn-primary') )
			superuser_btns.append( Submit('import-submit', _('Import Competition from File'), css_class = 'btn btn-primary') )
			button_args.extend( superuser_btns )
		
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
		
		def setLicenseChecks( self, request, competition ):
			return HttpResponseRedirect( pushUrl(request,'SetLicenseChecks', competition.id) )
		
		def __init__( self, *args, **kwargs ):
			system_info = SystemInfo.get_singleton()
		
			button_mask = kwargs.pop('button_mask', EDIT_BUTTONS)
			
			super(CompetitionForm, self).__init__(*args, **kwargs)
			self.helper = FormHelper( self )
			self.helper.form_action = '.'
			self.helper.form_class = 'form-inline'
			
			self.helper.layout = Layout(
				Row(
					Col(Field('name', size=30), 3),
					Col(Field('long_name', size=40), 4),
					Col(Field('description', size=50), 4),
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
					Col('category_format', 3),
					Col('discipline', 2),
					Col('race_class', 2),
					Col('legal_entity', 4),
				),
				Row(
					Col(Field('start_date', size=11), 2),
					Col(Field('number_of_days', size=3), 2),
					Col(Field('recurring'), 2),
					Col(Field('distance_unit'), 2),
				),
				Row(
					Col('number_set', 4),
					Col('seasons_pass', 4),
				),
				Row(
					Col(Field('using_tags'), 4),
					Col(Field('use_existing_tags'), 4),
					Col(Field('do_tag_validation'), 4),
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
				Row( HTML('<hr/><strong>Number Print Options:</strong>'), HTML('<div class="alert alert-info" role="info"><strong>Reminder:</strong> Set the <strong>Print Tag Option</strong> in <strong>System Info</strong> to enable printing.</div>') if system_info.print_tag_option == 0 else HTML(u''), ),
				Row(
					Col(Field('bib_label_print'),2),
					Col(Field('bibs_label_print'),2),
					Col(Field('bibs_laser_print'),2),
					Col(Field('shoulders_label_print'),2),
					Col(Field('frame_label_print'),2),
					Col(Field('frame_label_print_1'),2),
				),
				Row( HTML('<hr/>') ),
				Row(
					Col(Field('report_labels',size=8), 4),
					Col('ga_tracking_id', 4),
					Col(Field('show_signature'),4),
				),
				Row( HTML('<hr/>') ),
				Row(
					Col(Field('report_label_license_check'), 12)
				),
				Row( HTML('<hr/>') ),
				Field( 'license_check_note', type='hidden' ),
			)
			
			self.additional_buttons = []
			if button_mask == EDIT_BUTTONS:
				self.additional_buttons.append(
					('upload-prereg-list-submit', _('Upload Prereg List'), 'btn btn-success', self.uploadPrereg),
				)
				self.additional_buttons.append(
					('edit-report-labels-submit', _('Edit Report Labels'), 'btn btn-primary', self.editReportTags),
				)
				self.additional_buttons.append(
					('set-license-checks-submit', _('Set License Checks'), 'btn btn-primary', self.setLicenseChecks),
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
		
		if 'import-cloud-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'CompetitionCloudImportList') )
		
		if 'import-submit' in request.POST:
			return HttpResponseRedirect( pushUrl(request,'CompetitionImport') )
		
		if request.user.is_superuser:
			form = CompetitionSearchForm( request.POST, request=request )
			if form.is_valid():
				request.session['competition_filter'] = search_fields = form.cleaned_data
	else:
		if request.user.is_superuser:
			form = CompetitionSearchForm( initial=search_fields, request=request )
	
	competitions = Competition.objects.all().prefetch_related('report_labels')
	
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
		dNow = datetime.date.today()
		competitions = competitions.filter( start_date__gte = dNow - datetime.timedelta(days=120) )
		competitions = [c for c in competitions if not c.is_finished(dNow)]
	
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
	
	return HttpResponseRedirect(getContext(request, 'cancelUrl') + 'CompetitionEdit/{}/'.format(competition_new.id))
	
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
	system_info = SystemInfo.get_singleton()
	
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
	payload['license_holder_total'] = LicenseHolder.objects.filter( pk__in = Participant.objects.filter(competition=competition).distinct().values_list('license_holder__pk', flat=True) ).count()
	try:
		payload['transactionPeak'][0] = payload['transactionPeak'][0].strftime('%H:%M').lstrip('0')
	except:
		pass
		
	dates = [competition.start_date]
	finish_date = competition.finish_date
	while dates[-1] != finish_date:
		dates.append( dates[-1] + datetime.timedelta(days=1) )
	date_info = [{
			'license_holder_count': set(),
			'participant_count': set(),
			'day_of_count': set(),
		} for d in dates]
	date_i = {d:i for i, d in enumerate(dates)}
	for e in competition.get_events():
		di = date_info[date_i[timezone.localtime(e.date_time).date()]]
		di['license_holder_count'] |= set(LicenseHolder.objects.filter(pk__in=e.get_participants().values_list('license_holder',flat=True)).values_list('pk',flat=True))
		di['participant_count'] |= set(e.get_participants().values_list('pk',flat=True))
		di['day_of_count'] |= set(LicenseHolder.objects.filter(
				pk__in=e.get_participants().values_list('license_holder',flat=True)).filter(
				Q(license_code__startswith="TEMP") | Q(license_code__startswith="_") | Q(license_code__startswith="CP")
			).values_list('pk',flat=True))
	for di in date_info:
		di['license_holder_count'] = len(di['license_holder_count'])
		di['participant_count'] = len(di['participant_count'])
		di['day_of_count'] = len(di['day_of_count'])
		
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
			key=lambda p: (getCategorySeq(p), p.bib if p.bib else 99999, p.license_holder.search_text),
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
	page_title = u'{} - {}'.format( instance.competition.title, instance.name )
	return render( request, 'mass_start_start_list.html', locals() )
	
def get_annotated_waves( event ):
	try:
		waves = list(event.wave_set.all())
	except:
		waves = list(event.wavett_set.all())
		
	category_wave = {}
	for w in waves:
		for c in w.categories.all():
			category_wave[c] = w
			
	latest_reg_timestamp = event.date_time - datetime.timedelta( minutes=SystemInfo.get_reg_closure_minutes() )
	
	wave_starter_count = defaultdict( int )
	wave_bad_start_count = defaultdict( int )
	wave_late_reg_count = defaultdict( int )
	num_nationalities = defaultdict( set )
	for p in event.get_participants().defer('signature').select_related('license_holder','category'):
		w = category_wave[p.category]
		wave_starter_count[w] += 1
		if not p.can_start():
			wave_bad_start_count[w] += 1
		if p.registration_timestamp >= latest_reg_timestamp:
			wave_late_reg_count[w] += 1
		if p.license_holder.nation_code:
			num_nationalities[w].add( p.license_holder.nation_code )
		
	for w in waves:
		w.get_bad_start_count = wave_bad_start_count[w]
		w.get_starters_str = w.get_starters_str( wave_starter_count[w] )
		w.get_late_reg_count = wave_late_reg_count[w]
		w.get_num_nationalities = len(num_nationalities[w])
	
	return waves
	
@access_validation()
def StartListTT( request, eventTTId ):
	instance = get_object_or_404( EventTT, pk=eventTTId )
	time_stamp = datetime.datetime.now()
	page_title = u'{} - {}'.format( instance.competition.title, instance.name )
	wave_tts = get_annotated_waves( instance )
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
		timezone.localtime(event.date_time).strftime('%Y-%m-%d-%H%M%S'),
		timezone.now().strftime('%Y-%m-%d-%H%M%S'),
	)
	return response

def UCIExcelDownload( request, eventId, eventType, startList=1 ):
	eventType = int(eventType)
	event = get_object_or_404( [EventMassStart, EventTT][eventType], pk=eventId )
	startList = 1 if int(startList) else 0
	
	zip_fname = 'RaceDB-UCI-{}-{}-{}_{}.zip'.format(
		['Results','StartList'][startList],
		utils.cleanFileName(event.competition.name),
		utils.cleanFileName(event.name),
		datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'),
	)
	
	# Create a temp file.
	zip_stream = tempfile.TemporaryFile()
	
	zip_handler = zipfile.ZipFile( zip_stream, 'w' )
	for category in event.get_categories():
		fname = 'RaceDB-UCI-{}-{}-{}-{}.xlsx'.format(
			['Results','StartList'][startList],
			utils.cleanFileName(event.competition.name),
			utils.cleanFileName(event.name),
			utils.cleanFileName(category.code_gender),
		)
		safe_print( u'adding', fname, '...' )
		zip_handler.writestr( fname, uci_excel(event, category, startList) )

	zip_handler.close()

	zip_stream.seek( 0 )	
	response = HttpResponse(zip_stream, content_type=" application/zip")
	zip_stream.seek( 0, 2 )
	response['Content-Length'] = '{}'.format(zip_stream.tell())
	zip_stream.seek( 0 )	
	response['Content-Disposition'] = 'attachment; filename={}'.format(zip_fname)
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
	message_stream = StringIO()
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
	set_team_all_disciplines = forms.BooleanField( required=False, label=_('Update Default Team for all Disciplines'), )
	update_license_codes = forms.BooleanField( required=False, label=_('Update License Codes based on First Name, Last Name, Date of Birth, Gender match'),
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
				Field('set_team_all_disciplines'),
			),
			Row(
				Field('update_license_codes'),
			),
		)

		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_license_holder_import_excel( excel_contents, update_license_codes, set_team_all_disciplines ):
	worksheet_contents = excel_contents.read()
	message_stream = StringIO()
	license_holder_import_excel(
		worksheet_contents=worksheet_contents,
		message_stream=message_stream,
		update_license_codes=update_license_codes,
		set_team_all_disciplines=set_team_all_disciplines,
	)
	results_str = message_stream.getvalue()
	return license_holder_msg_to_html(results_str)
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def LicenseHoldersImportExcel( request ):
	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
		form = ImportExcelForm(request.POST, request.FILES)
		if form.is_valid():
			results_str = handle_license_holder_import_excel(
				request.FILES['excel_file'],
				form.cleaned_data['update_license_codes'],
				form.cleaned_data['set_team_all_disciplines'],
			)
			return render( request, 'license_holder_import_excel.html', locals() )
	else:
		form = ImportExcelForm( initial={'set_team_all_disciplines': True} )
	
	return render( request, 'license_holder_import_excel.html', locals() )

#-----------------------------------------------------------------------
def get_compressed_license_holder_json():
	# Create a temp file.
	gzip_stream = tempfile.TemporaryFile()
	# Create a gzip and connect it to the temp file.
	gzip_handler = gzip.GzipFile( fileobj=gzip_stream, mode="wb", filename='{}.json'.format('license_holders') )
	# Write the json to the gzip obj, which compresses it and writes it to the temp file.
	license_holder_export( gzip_handler )
	# Make sure gzip flushes all its buffers.
	gzip_handler.flush()
	gzip_handler.close()	# Does not close underlying fileobj.
	return gzip_stream

def handle_export_license_holders():
	gzip_stream = get_compressed_license_holder_json()
		
	# Generate the response using the file wrapper, content type: x-gzip
	# Since this file can be big, best to use the StreamingHTTPResponse
	# that way we can guarantee that the file will be sent entirely.
	response = StreamingHttpResponse( gzip_stream, content_type='application/x-gzip' )

	# Content size
	gzip_stream.seek(0, 2)
	response['Content-Length'] = '{}'.format(gzip_stream.tell())
	response['Authorization'] = authorization.get_secret_authorization()
	gzip_stream.seek( 0 )

	# Add content disposition so the browser will download the file.
	response['Content-Disposition'] = 'attachment; filename={}.gz'.format('license_holder')

	# Send back the response to the request.
	return response	

def LicenseHolderCloudDownload( request ):
	if not authorization.validate_secret_request(request):
		return HttpResponseForbidden()
	
	safe_print( u'LicenseHolderCloudDownload: processing...' )
	response = handle_export_license_holders()
	safe_print( u'LicenseHolderCloudDownload: response returned.' )
	response['Authorization'] = authorization.get_secret_authorization()
	return response

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def LicenseHoldersCloudImport( request, confirmed=False ):
	if confirmed:
		url = SystemInfo.get_singleton().get_cloud_server_url( 'LicenseHolderCloudDownload' )
		safe_print( u'LicenseHoldersCloudImport: sending request to:', url )
		
		response = requests.get( url, stream=True, headers={'Authorization':authorization.get_secret_authorization()} )
		
		errors = []
		try:
			response.raise_for_status()
		except Exception as e:
			safe_print( u'LicenseHoldersCloudImport: ', e )
			errors.append( e )
		
		if not errors:
			safe_print( u'LicenseHoldersCloudImport: received response from:', url )
			try:
				# Download the content and save it into a temporary file.
				gzip_stream = tempfile.TemporaryFile()
				for c in response.iter_content(None):
					gzip_stream.write( c )
				gzip_stream.seek( 0 )
				# Unzip the content and do the import.
				gzip_handler = gzip.GzipFile( fileobj=gzip_stream, mode='rb' )
				license_holder_import( gzip_handler )
			except Exception as e:
				safe_print( u'LicenseHoldersCloudImport: ', e )
				errors.append( e )
		
		return render( request, 'license_holder_cloud_import.html', locals() )
		
	page_title = _('Import all License Holders from Cloud Server')
	message = _("This will add/update all License Holders in this database to match the Cloud Server..")
	cancel_target = getContext(request,'popUrl')
	target = getContext(request,'path') + '1/'
	return render( request, 'are_you_sure.html', locals() )
	
#-----------------------------------------------------------------------

competition_fields = ('id', 'date_range_year_str', 'name', 'city', 'stateProv', 'number_of_days', 'organizer', 'has_results')
competition_name_fields = ('category_format', 'discipline', 'race_class')
def CompetitionCloudQuery( request ):
	if not authorization.validate_secret_request(request):
		return HttpResponseForbidden()
	
	# Gets all Competitions from up to a year ago.
	d_ref = (timezone.now() - datetime.timedelta(days=366*2)).date()
	competitions = Competition.objects.filter( start_date__gte=d_ref
		).select_related('category_format','discipline','race_class').order_by('-start_date')
	
	response = []
	for c in competitions:
		r = {a:getattr(c,a) for a in competition_fields}
		r.update( {a:getattr(c,a).name for a in competition_name_fields} )
		r['start_date'] = c.start_date.strftime('%Y-%m-%d')
		response.append( r )
	
	return JsonResponse(response, safe=False)

def CompetitionCloudExport( request, competitionId ):
	if not authorization.validate_secret_request(request):
		return HttpResponseForbidden()
	
	competition = get_object_or_404( Competition, pk=competitionId )
	safe_print( u'CompetitionCloudExport: processing Competition id:', competitionId )
	response = handle_export_competition( competition )
	safe_print( u'CompetitionCloudExport: processing completed.' )
	return response

class CompetitionCloudForm( Form ):
	selected		= forms.BooleanField( required=False, label='' )
	id				= forms.IntegerField( widget=forms.HiddenInput() )
	
	def __init__( self, *args, **kwargs ):
		initial = kwargs.get('initial', {})
		self.competition_fields = {}
		for k in list(initial.iterkeys()):
			if k not in ('id', 'selected'):
				self.competition_fields[k] = initial.pop(k)
		super(CompetitionCloudForm, self).__init__( *args, **kwargs )

	output_hdrs   = (_('Local'), _('Dates'),      _('Discipline'), _('Name'), _('Class'), _('Organizer'), _('City'), _('Results') )
	output_fields = (  'local', 'date_range_year_str', 'discipline',    'name', 'race_class',   'organizer',    'city',  'has_results')
	output_bool_fields = set(['local', 'has_results'])
	
	def as_table( self ):
		s = StringIO()
		for f in self.output_fields:
			if f in self.output_bool_fields:
				v = int(self.competition_fields.get(f,False))
				s.write( u'<td class="text-center"><span class="{}"></span></td>'.format(['blank', 'is-good'][v]) )
			else:
				s.write( u'<td>{}</td>'.format(escape(unicode(self.competition_fields.get(f,u'')))) )
		p = super(CompetitionCloudForm, self).as_table().replace( '<th></th>', '' ).replace( '<td>', '<td class="text-center">', 1 )
		ln = len('</tr>')
		return mark_safe( p[:-ln] + s.getvalue() + p[-ln:] )
		
CompetitionCloudFormSet = formset_factory(CompetitionCloudForm, extra=0, max_num=100000)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def CompetitionCloudImportList( request ):
	headers = [_('Import')] + list(CompetitionCloudForm.output_hdrs)
	if request.method == 'POST':
		form_set = CompetitionCloudFormSet( request.POST )
		if form_set.is_valid():
			success = False
			for d in form_set.cleaned_data:
				if not d['selected']:
					continue
				
				url = SystemInfo.get_singleton().get_cloud_server_url( 'CompetitionCloudExport/{}'.format(d['id']) )
				print 'CompetitionCloudImportList: sending request:', url
				response = requests.get( url, stream=True, headers={'Authorization':authorization.get_secret_authorization()} )
				gzip_stream = tempfile.TemporaryFile()
				for c in response.iter_content(None):
					gzip_stream.write( c )
				gzip_stream.seek( 0 )
				
				# Unzip the content and do the import.
				print 'CompetitionCloudImportList: processing content...'
				gzip_handler = gzip.GzipFile( fileobj=gzip_stream, mode='rb' )
				competition_import( gzip_handler )
				success = True
			
			if success:
				return HttpResponseRedirect(getContext(request,'cancelUrl') + 'LicenseHoldersCloudImport/1/' )
			return HttpResponseRedirect( getContext(request,'cancelUrl') )
	else:
		url = SystemInfo.get_singleton().get_cloud_server_url( 'CompetitionCloudQuery' )
		safe_print( u'CompetitionCloudImportList: sending request:', url )
		response = requests.get( url, headers={'Authorization':authorization.get_secret_authorization()} )
		
		cloud_competitions = response.json()
		for c in cloud_competitions:
			d = datetime.date(*[int(v) for v in c['start_date'].split('-')])
			c['local'] = Competition.objects.filter( name=c['name'], start_date=d ).exists()
		form_set = CompetitionCloudFormSet( initial=cloud_competitions )
	return render( request, 'competition_import_cloud_list.html', locals() )

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
	competition = instance.competition
	if request.method == 'POST':
		adjustment_formset = AdjustmentFormSet( request.POST )
		reNum = re.compile( '[^0-9]' )
		if adjustment_formset.is_valid():
			def get_eda():
				''' Get the entry_tt, direction and adjustment for each line in the form. '''
				''' Also commit the est_speed to the entry. '''
				entries = { int(ett.pk):ett for ett in EntryTT.objects.filter(event=instance).select_related('participant').defer('participant__signature') }
				
				eda = []
				for d in adjustment_formset.cleaned_data:
					pk = d['entry_tt_pk']
					try:
						pk = int(pk)
					except ValueError:
						pass
					
					try:
						entry_tt = entries[pk]
					except KeyError:
						continue
					
					participant_changed = False
					
					try:
						est_kmh = competition.to_kmh(float(d['est_speed']))
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
					if adjustment:
						direction = adjustment[0] if adjustment[0] in ('+','-','r','s','e') else 'e'
					else:
						direction = None
					try:
						adjustment = int( reNum.sub(u'', adjustment) )
					except ValueError:
						adjustment = None
					
					if not adjustment:
						direction, adjustment = None, None
					
					eda.append( (entry_tt, direction, adjustment) )

				return eda
			
			if "apply_adjustments" in request.POST:
				eda = get_eda()
			
				def safe_i( i ):
					return min( max(i, 0), len(eda) - 1 )
				
				def swap( i, j ):
					eda[i][0].swap_position( eda[j][0] )
					eda[i], eda[j] = eda[j], eda[i]
				
				def move_to( i, iNew ):
					i, iNew = safe_i(i), safe_i(iNew)
					dir = -1 if iNew < i else 1
					while i != iNew:
						swap( i, i+dir )
						i += dir
				
				# Process all random entries.
				i_rand = []	# Only randomize with other random positions.
				for i, (entry_tt, direction, adjustment) in enumerate(eda):
					if direction == 'r':
						i_rand.append( i )
				for i in i_rand:
					swap( i_rand[i], i_rand[random.randint(0,len(i_rand)-1)] )
				del i_rand
				
				# Process relative moves by bubbling.
				for i in xrange(len(eda)):
					entry_tt, direction, adjustment = eda[i]
					if direction == '-':				# Move backwards going forward.
						move_to( i, i - adjustment )				
				for i in xrange(len(eda)-1, -1, -1):
					entry_tt, direction, adjustment = eda[i]
					if direction == '+':				# Move forward going backwards.
						move_to( i, i + adjustment )
				
				# Process absolute starts.
				for i in xrange(len(eda)):
					entry_tt, direction, adjustment = eda[i]
					if direction == 's' and adjustment-1 < i:	# Move backwards going forward.
						move_to( i, adjustment-1 )
				for i in xrange(len(eda)-1, -1, -1):
					entry_tt, direction, adjustment = eda[i]
					if direction == 's' and adjustment-1 > i:	# Move backwards going forward.
						move_to( i, adjustment-1 )
				
				# Process absolute ends.
				for i in xrange(len(eda)):
					entry_tt, direction, adjustment = eda[i]
					if direction == 'e' and len(eda) - adjustment < i:
						move_to( i, len(eda) - adjustment )
				for i in xrange(len(eda)-1, -1, -1):
					entry_tt, direction, adjustment = eda[i]
					if direction == 'e' and len(eda) - adjustment > i:
						move_to( i, len(eda) - adjustment )
			
				# And save it.
				with BulkSave() as bs:
					for e in eda:
						bs.append( e[0] )
					
			if "regenerate_start_times" in request.POST:
				instance.create_initial_seeding()
	
	instance.repair_seeding()
	entry_tts=list(instance.entrytt_set.all())
	for e in entry_tts:
		e.clock_time = instance.date_time + e.start_time
	adjustment_formset = AdjustmentFormSet( entry_tts=entry_tts )
	wave_tts = get_annotated_waves( instance )
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
	
	def newCustomCategoryCB( self, request, eventMassStart ):
		return HttpResponseRedirect( pushUrl(request,'CustomCategoryNew',eventMassStart.id, eventMassStart.event_type) )
	
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
			self.additional_buttons.extend( [
				('custom-category-submit', _('New Custom Category'), 'btn btn-success', self.newCustomCategoryCB),
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
		timezone.localtime(eventMassStart.date_time).strftime('%Y-%m-%d'),
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
	
	safe_print( u'UploadCrossMgr: processing...' )
	if payload:
		response = read_results.read_results_crossmgr( payload )
	safe_print( u'UploadCrossMgr: Done.' )
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

def pre_edit_fix_wave_distance( wave ):
	if wave.distance and wave.event.competition.distance_unit == 1:
		wave.distance /= 1.609344
	
def pre_save_fix_wave_distance( wave ):
	if wave.distance and wave.event.competition.distance_unit == 1:
		wave.distance *= 1.609344
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveNew( request, eventMassStartId ):
	event_mass_start = get_object_or_404( EventMassStart, pk=eventMassStartId )
	
	waves_existing = list( event_mass_start.wave_set.all() )
	wave = Wave( event = event_mass_start )
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
	wave.save()
	
	return HttpResponseRedirect( popPushUrl(request,'WaveEdit',wave.id) )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveEdit( request, waveId ):
	wave = get_object_or_404( Wave, pk=waveId )
	return GenericEdit( Wave, request, waveId, GetWaveForm(wave.event, wave),
		template = 'wave_form.html',
		pre_edit_func=pre_edit_fix_wave_distance, pre_save_func=pre_save_fix_wave_distance,
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveDelete( request, waveId ):
	wave = get_object_or_404( Wave, pk=waveId )
	return GenericDelete( Wave, request, waveId, GetWaveForm(wave.event, wave),
		template = 'wave_form.html',
		pre_edit_func=pre_edit_fix_wave_distance,
	)

#-----------------------------------------------------------------------

@autostrip
class EventTTForm( ModelForm ):
	class Meta:
		model = EventTT
		fields = '__all__'
	
	def newWaveTTCB( self, request, eventTT ):
		return HttpResponseRedirect( pushUrl(request,'WaveTTNew',eventTT.id) )
	
	def newCustomCategoryCB( self, request, eventTT ):
		return HttpResponseRedirect( pushUrl(request,'CustomCategoryNew',eventTT.id, eventTT.event_type) )
	
	def applyToParticipantsCB( self, request, eventMassStart ):
		return HttpResponseRedirect( pushUrl(request,'EventApplyToExistingParticipants',eventMassStart.id) )
		
	def seedingCB( self, request, eventTT ):
		return HttpResponseRedirect( pushUrl(request,'StartListTT',eventTT.id) )		
	
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
			Row(
				Col(Field('group_size'), 4),
				Col(Field('group_size_gap'), 4),
			),
			Row( Col(Field('road_race_finish_times'),4), Col(Field('dnsNoData'),4) ),
			Row( Field('note', rows='4', cols='60') ),
		)
		self.additional_buttons = []
		if button_mask == EDIT_BUTTONS:
			self.additional_buttons.extend( [
				('new-wave-submit', _('New TT Wave'), 'btn btn-success', self.newWaveTTCB),
			] )
			self.additional_buttons.extend( [
				('custom-category-submit', _('New Custom Category'), 'btn btn-success', self.newCustomCategoryCB),
			] )
			self.additional_buttons.extend( [
				('seeding-submit', _('Edit Seeding'), 'btn btn-success', self.seedingCB),
			] )
			instance = getattr(self, 'instance', None)
			if instance and instance.optional and instance.competition.has_participants():
				self.additional_buttons.extend( [
					('apply-to-participants-submit', _('Apply "Select by Default" to Existing Participants'), 'btn btn-success', self.applyToParticipantsCB),
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
			instance = form.save( commit=False )
			instance.save()
			
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
		template = 'event_tt_form.html',
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
		timezone.localtime(eventTT.date_time).strftime('%Y-%m-%d'),
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
			
			series_for_seeding_field = self.fields['series_for_seeding']
			series_for_seeding_field.choices = [(u'', u'----')] + [
				(series.id, series.name) for series in Series.objects.filter(category_format=event_tt.competition.category_format)
			]
			
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
					Col(Field('sequence_option'), 3),
					Col(Field('series_for_seeding'), 3),
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
	
	wave_tts_existing = list( event_tt.wavett_set.all() )
	wave_tt = WaveTT( event = event_tt )
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
	wave_tt.save()
	
	return HttpResponseRedirect( popPushUrl(request,'WaveTTEdit',wave_tt.id) )

@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveTTEdit( request, waveTTId ):
	wave_tt = get_object_or_404( WaveTT, pk=waveTTId )
	return GenericEdit( WaveTT, request, waveTTId, GetWaveTTForm(wave_tt.event, wave_tt),
		template = 'wave_tt_form.html',
		pre_edit_func=pre_edit_fix_wave_distance, pre_save_func=pre_save_fix_wave_distance,
	)
	
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def WaveTTDelete( request, waveTTId ):
	wave_tt = get_object_or_404( WaveTT, pk=waveTTId )
	return GenericDelete( WaveTT, request, waveTTId, GetWaveTTForm(wave_tt.event, wave_tt),
		template = 'wave_tt_form.html',
		pre_edit_func=pre_edit_fix_wave_distance,
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

@access_validation()
def LicenseHolderAddConfirm( request, competitionId, licenseHolderId, tag_checked=0 ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	competition_age = competition.competition_age( license_holder )
	try:
		tag_checked = int(tag_checked)
	except:
		tag_checked = 0
	return render( request, 'license_holder_add_confirm.html', locals() )

@access_validation()
def LicenseHolderConfirmAddToCompetition( request, competitionId, licenseHolderId, tag_checked=0 ):
	competition = get_object_or_404( Competition, pk=competitionId )
	license_holder = get_object_or_404( LicenseHolder, pk=licenseHolderId )
	try:
		tag_checked = int(tag_checked)
	except:
		tag_checked = 0
	
	# Try to create a new participant from the license_holder.
	participant = Participant( competition=competition, license_holder=license_holder, preregistered=False ).init_default_values()
	participant.tag_checked = bool( tag_checked )
	try:
		participant.auto_confirm().save()
		participant.add_to_default_optional_events()
		return HttpResponseRedirect(pushUrl(request, 'ParticipantEdit', participant.id, cancelUrl=True))
	except IntegrityError as e:
		# If this participant exists already, recover silently by going directly to the existing participant.
		participant = Participant.objects.filter(competition=competition, license_holder=license_holder).first()
		if participant:
			if tag_checked and not participant.tag_checked:
				participant.tag_checked = True
				participant.save()
			return HttpResponseRedirect(pushUrl(request, 'ParticipantEdit', participant.id, cancelUrl=True))
		else:
			# Integrity error, but not a duplicate?  Something weird going on.
			error = _('Integrity Error')
			context = '{}\n\n{}'.format( e, traceback.format_exc() )
			href = getContext(request,'cancelUrl')
			return render( request, 'generic_error.html', locals() )

#-----------------------------------------------------------------------
	
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
				Col(Field('tag_creation'), 6),
			),
			Row(
				Col(Field('tag_bits'), 4),
				Col(Field('tag_template', size=28), 4),
				Col(Field('tag_from_license_id'), 4),
			),
			Row(
				Col(Field('tag_all_hex'), 6),
			),
			HTML( '<hr/>' ),
			Row(
				Col(Field('print_tag_option'), 4),
				Col(Field('server_print_tag_cmd', size=80), 8),				
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
				Col(Field('license_holder_unique_by_license_code'), 6),
			),
			Row(
				Col(Field('cloud_server_url', size=80), 6),
			),
			HTML( '<hr/>' ),
			Field( 'rfid_server_host', type='hidden' ),
			Field( 'rfid_server_port', type='hidden' ),
			Field( 'tag_from_license', type='hidden' ),
		)
		addFormButtons( self, button_mask )
		
@access_validation()
@user_passes_test( lambda u: u.is_superuser )
def SystemInfoEdit( request ):
	return GenericEdit( SystemInfo, request, SystemInfo.get_singleton().id, SystemInfoForm )
	
@access_validation()
def UpdateLogShow( request ):
	update_log = UpdateLog.objects.all()
	return render( request, 'update_log_show.html', locals() )
	
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
						Row( Field('start_date', size=10) ),
						Row( Field('end_date', size=10) ),
						css_class = 'col-md-1'
					),
					Div(
						Row(
							Field('race_classes', id='focus', size=10, style="width: 13em;"),
							Field('disciplines', size=10, style="width: 13em;"),
							Field('organizers', size=10, style="width: 13em;"),
							Field('include_labels', size=10, style="width: 13em;"),
							Field('exclude_labels', size=10, style="width: 13em;"),
						),
						Row( HTML( _('Use Ctrl-Click to Multi-Select and Ctrl-Click to Deselect') ) ),
						css_class = 'col-md-11',
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
		
			payload, license_holders_event_errors, competitions = participation_data( **initial )
			payload_json = json.dumps(payload, separators=(',',':'))
	else:
		payload, license_holders_event_errors, competitions = participation_data( **initial )
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
		date = timezone.now().date()
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
from competition_import_export import license_holder_import, license_holder_export
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
			Row(HTML('Cloud Server URL: <strong>"' + url + '"</strong> <a class="btn btn-xs btn-primary" href="./SystemInfoEdit/">SystemInfo</a>') if url else HTML(_('To Export to Cloud Race, configure <strong>Cloud Server URL</strong> in <a class="btn btn-xs btn-primary" href="./SystemInfoEdit/">SystemInfo</a>')) )
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
	response['Content-Length'] = '{}'.format(gzip_stream.tell())
	response['Authorization'] = authorization.get_secret_authorization()
	gzip_stream.seek( 0 )

	# Add content disposition so the browser will download the file.
	response['Content-Disposition'] = 'attachment; filename={}.gz'.format(competition.get_filename_base())

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
			if 'ok-cloud-submit' in request.POST:
				gzip_stream = get_compressed_competition_json(
					competition,
					form.cleaned_data['export_as_template'],
					form.cleaned_data['remove_ftp_info'],
				)
				gzip_stream.seek(0, 2)
				headers = {
					'Content-Length': '{}'.format(gzip_stream.tell()),
					'Content-Type': 'application/octet-stream',
					'Authorization': authorization.get_secret_authorization(),
				}
				gzip_stream.seek(0, 0)
				url = SystemInfo.get_singleton().get_cloud_server_url( 'CompetitionCloudUpload' )			
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
	json_file = forms.FileField( required=True, label=_('Competition File (*.gz|*.gzip|*.json)') )
	
	name = forms.CharField( required=False, label=_('Change Name to'), help_text=_('Leave blank to use Competition name in import file') )
	start_date = forms.DateField( required=False, label=_('Change Start Date to'), help_text=_('Leave blank to use Competition date in import file') )
	replace = forms.BooleanField( required=False, label=_('Replace existing Competition with same Name and Start Date') )
	import_as_template = forms.BooleanField( required=False, label=_('Import as Template (ignore Participants and Teams)') )
	
	def __init__( self, *args, **kwargs ):
		super( ImportCompetitionForm, self ).__init__( *args, **kwargs )
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'
		
		self.helper.layout = Layout(
			Row(Field('json_file', accept=".gz,.gzip,.json")),
			Row(HTML('&nbsp;')),
			Row(Col(Field('name', size=50), 6), Col(Field('start_date'), 3)),
			Row(Col(Field('replace'), 4), Col(Field('import_as_template'), 4)),
		)
		
		addFormButtons( self, OK_BUTTON | CANCEL_BUTTON, cancel_alias=_('Done') )

def handle_import_competition( json_file_request, import_as_template=False, name=None, start_date=None, replace=False ):
	try:
		if json_file_request.name.endswith('.gzip') or json_file_request.name.endswith('.gz'):
			json_file_request = gzip.GzipFile(filename=json_file_request.name, fileobj=json_file_request, mode='rb')
	except Exception as e:
		pass
		
	message_stream = StringIO()
		
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
				form.cleaned_data['replace'],
			)
			return render( request, 'import_competition.html', locals() )
	else:
		form = ImportCompetitionForm()
	
	return render( request, 'import_competition.html', locals() )
	
@csrf_exempt
def CompetitionCloudUpload( request ):
	safe_print( u'CompetitionCloudUpload: processing...' )
	response = {'errors':[], 'warnings':[], 'message':''}
	if request.method == "POST":
		if not authorization.validate_secret_request( request ):
			response['errors'].append( 'Authorization Error' )
		else:
			try:
				gzip_handler = gzip.GzipFile(fileobj=StringIO(request.body), mode='rb')
				response['message'] = handle_import_competition( gzip_handler, import_as_template=False, replace=True )
			except Exception as e:
				response['errors'].append( 'Competition Upload Error: {}'.format(e) )
	else:
		response['errors'].append( u'Request must be of type POST with gzip json payload.' )
	safe_print( u'CompetitionCloudUpload: done.' )
	safe_print( response['message'] )
	for e in response['errors']:
		safe_print( u'Error:', e )
	for w in response['warnings']:
		safe_print( u'Error:', w )
	return JsonResponse( response )

#-----------------------------------------------------------------------
def Resequence( request, modelClassName, instanceId, newSequence ):
	newSequence = int(newSequence)
	cls = globals()[modelClassName]
	instance = get_object_or_404( cls, pk=instanceId )
	
	try:
		instance.move_to( newSequence )
	except AttributeError:
		objs = list(cls.objects.all().order_by('sequence'))
		newSequence = max(0, min(newSequence, len(objs)) )
		objs.remove( instance )
		objs.insert( newSequence, instance )
		with transaction.atomic():
			for i, obj in enumerate(objs, 1):
				if obj.sequence != i:
					obj.sequence = i
					obj.save()
	return HttpResponseRedirect(getContext(request,'cancelUrl'))

#-----------------------------------------------------------------------
def PastCompetition( request ):
	return render( request, 'past_competition.html', locals() )

#-----------------------------------------------------------------------

def Logout( request ):
	return logout( request, next_page=getContext(request, 'cancelUrl') )
