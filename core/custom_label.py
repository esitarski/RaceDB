from views_common import *
from django.utils.translation import ugettext_lazy as _
import utils

from views import print_pdf
from print_bib import print_bib_tag_label, print_body_bib, print_shoulder_bib

@autostrip
class CustomLabelForm( Form ):
	text = forms.CharField( required = False, label = _('Text'), help_text = _('Text to be printed on the Custom Label') )
		
	def __init__( self, *args, **kwargs ):
		system_info = kwargs.pop( 'system_info' )
		c = kwargs.pop( 'competition' )

		super(CustomLabelForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper( self )
		self.helper.form_action = '.'
		self.helper.form_class = 'form-inline'

		additional_buttons = []
		if system_info.print_tag_option != 0 and c.any_print:
			if c.bib_label_print:
				additional_buttons.append( ('print-body-bib-1', _('1 Body Bib'), 'btn btn-primary') )
			if c.bibs_label_print:
				additional_buttons.append( ('print-body-bib-2', _('2 Body Bibs'), 'btn btn-primary') )
			if c.bibs_laser_print:
				additional_buttons.append( ('print-body-bib-2-1', _('2 Body Bibs'), 'btn btn-primary') )
			if c.shoulders_label_print:
				additional_buttons.append( ('print-shoulder-bib', _('2 Shoulder Nums'), 'btn btn-primary') )
			if c.frame_label_print:
				additional_buttons.append( ('print-frame-bib', _('2 Frame Nums'), 'btn btn-primary') )
		
		self.helper.layout = Layout(
			Row(
				Col(Field('text', size=8), 12),
			),
		)
		addFormButtons( self, button_mask=CANCEL_BUTTON, additional_buttons=additional_buttons )

class CustomLicenseHolder( object ):
	def __init__( self, last_name ):
		self.last_name = self.first_last = self.first_last_short = last_name
	
	def __getattr__( self, name ):
		return u''
	
class CustomParticipant( object ):
	def __init__( self, bib, competition ):
		self.bib = bib
		self.competition = competition
		self.license_holder = CustomLicenseHolder( bib )
		self.category = None
		self.team = None
	
	def __getattr__( self, name ):
		return u''

@access_validation()
def CustomLabel( request, competitionId ):
	competition = get_object_or_404( Competition, pk=competitionId )
	
	custom_label_text = unicode(request.session.get('custom_label_text', u''))

	if request.method == 'POST':
		if 'cancel-submit' in request.POST:
			return HttpResponseRedirect(getContext(request,'cancelUrl'))
			
		form = CustomLabelForm( request.POST, system_info=SystemInfo.get_singleton(), competition=competition )
		if form.is_valid():
			text = form.cleaned_data['text'].upper()
			text = utils.cleanFileName( text )
			request.session['custom_label_text'] = custom_label_text = text
			
			# Duck type the bib interface.
			participant = CustomParticipant( text, competition )
			
			if 'print-body-bib-1' in request.POST:
				return print_pdf( request, participant, print_body_bib(participant, 1, False), 'Body' )
			elif 'print-body-bib-2' in request.POST:
				return print_pdf( request, participant, print_body_bib(participant, 2, False), 'Body' )
			elif 'print-body-bib-2-1' in request.POST:
				return print_pdf( request, participant, print_body_bib(participant, 2, True), 'Body' )
			elif 'print-shoulder-bib' in request.POST:
				return print_pdf( request, participant, print_shoulder_bib(participant), 'Shoulder' )
			elif 'print-frame-bib' in request.POST:
				return print_pdf( request, participant, print_bib_tag_label(participant), 'Frame' )
			
	else:
		form = CustomLabelForm( system_info=SystemInfo.get_singleton(), competition=competition, initial={'text':custom_label_text} )
		
	return render( request, 'custom_label.html', locals() )
