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
				return render_to_response( 'rfid_write_status.html', RequestContext(request, locals()) )
			
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
						return render_to_response( 'rfid_validate.html', RequestContext(request, locals()) )
					else:
						# Handle writing the tag.
						status, response = WriteTag(tag, rfid_antenna)
						if not status:
							status_entries = [
								(_('Tag Write Failure'), response.get('errors',[]) ),
							]
				
				if not status:
					return render_to_response( 'rfid_write_status.html', RequestContext(request, locals()) )
				# if status: fall through to ok-submit case.
			
			# ok-submit
			if 'auto-generate-tag-submit' in request.POST:
				return HttpResponseRedirect(getContext(request,'path'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = LicenseHolderTagForm( initial = dict(tag=license_holder.existing_tag, rfid_antenna=rfid_antenna) )
		
	return render_to_response( 'license_holder_tag_change.html', RequestContext(request, locals()) )

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
		
		self.helper.layout = Layout(
			#Field( 'id', type='hidden' ),
			Row(
				Col(Field('last_name', size=40), 4),
				Col(Field('first_name', size=40), 4),
				Col('gender', 2),
				ColKey(
					HTML('<img src="{}"/>'.format(static('images/warning.png') if lh and lh.date_of_birth_error else '')),
					Field('date_of_birth', size=10),
					HTML(error_html(lh and lh.date_of_birth_error)),
					cols=2),
			),
			Row(
				Col(Field('city', size=40), 3),
				Col(Field('state_prov', size=40), 3),
				Col(Field('nationality', size=40), 3),
				Col(Field('zip_postal', size=10), 3),
			),
			Row(
				Col(Field('email', size=50), 4),
				Col(Field('phone', size=50), 4),
			),
			Row(
				ColKey(
					HTML('<img src="{}"/>'.format(static('images/warning.png') if lh and lh.license_code_error else '')),
					Field('license_code'),
					HTML(error_html(lh and lh.license_code_error)),
					cols=3),
				ColKey(
					HTML('<img src="{}"/>'.format(static('images/warning.png') if lh and lh.uci_code_error else '')),
					Field('uci_code'),
					HTML(error_html(lh and lh.uci_code_error)),
					cols=9),
			),
			Row(
				Col('existing_tag', 3),
				Col('existing_tag2', 3),
				Col('active', 3),
			),
			Row(
				Col(Field('emergency_contact_name', size=50), 4),
				Col(Field('emergency_contact_phone'), 4),
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
				license_holders = [LicenseHolder.objects.get(Q(license_code=arg) | Q(uci_code=arg) | Q(existing_tag=arg) | Q(existing_tag2=arg))]
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
	return render_to_response( 'license_holder_list.html', RequestContext(request, locals()) )

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
		
	return render_to_response( 'license_holder_scan_form.html', RequestContext(request, locals()) )

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

#--------------------------------------------------------------------------
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
				return render_to_response( 'license_holder_scan_rfid.html', RequestContext(request, locals()) )
			
			request.session['license_holder_filter'] = u'rfid={}'.format(tag.lstrip('0'))
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
	else:
		form = RfidScanForm( initial=dict(rfid_antenna=rfid_antenna) )
		
	return render_to_response( 'license_holder_scan_rfid.html', RequestContext(request, locals()) )

#------------------------------------------------------------------------------------------------------
@access_validation()
def LicenseHoldersCorrectErrors( request ):
	license_holders = LicenseHolder.get_errors()
	isEdit = True
	return render_to_response( 'license_holder_correct_errors_list.html', RequestContext(request, locals()) )

#------------------------------------------------------------------------------------------------------
@access_validation()
def LicenseHoldersManageDuplicates( request ):
	duplicates = LicenseHolder.get_duplicates()
	return render_to_response( 'license_holder_duplicate_list.html', RequestContext(request, locals()) )

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
	return render_to_response( 'license_holder_select_duplicates.html', RequestContext(request, locals()) )
	
@access_validation()
def LicenseHoldersSelectMergeDuplicate( request, duplicateIds ):
	pks = [int(pk) for pk in duplicateIds.split(',')]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	return render_to_response( 'license_holder_select_merge_duplicate.html', RequestContext(request, locals()) )

@access_validation()
def LicenseHoldersMergeDuplicates( request, mergeId, duplicateIds ):
	license_holder_merge = get_object_or_404( LicenseHolder, pk=mergeId )
	pks = [int(pk) for pk in duplicateIds.split(',')]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	return render_to_response( 'license_holder_select_merge_duplicate_confirm.html', RequestContext(request, locals()) )

def LicenseHoldersMergeDuplicatesOK( request, mergeId, duplicateIds ):
	license_holder_merge = get_object_or_404( LicenseHolder, pk=mergeId )
	pks = [int(pk) for pk in duplicateIds.split(',')]
	pks = [pk for pk in pks if pk != license_holder_merge.pk]
	duplicates = LicenseHolder.objects.filter(pk__in=pks).order_by('search_text')
	if duplicates.count() != len(pks):
		return HttpResponseRedirect(getContext(request,'cancelUrl'))
	license_holder_merge_duplicates( license_holder_merge, duplicates )
	return HttpResponseRedirect(getContext(request,'cancelUrl'))
	
#------------------------------------------------------------------------------------------------------
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
	
