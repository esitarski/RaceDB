from django.utils.translation import ugettext_lazy as _

import os
import copy
import math
import getpass
import glob

from models import *
from pdf import PDF
from encode_code128 import encode_code128

inches_to_points = 72.0

def has_descenders( text ):
	return any( d in text for d in 'jygpq' )
	
def get_font_file( fname ):
	parent = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
	return os.path.join(parent, 'fonts', fname)

def reset_font_cache():
	font_cache = os.path.dirname( get_font_file('base.ttf') )
	for f in glob.iglob( os.path.join(font_cache, '*.pkl') ):
		os.remove( f )

barcode_width_max = 2.5*inches_to_points
def draw_code128( pdf, text, x, y, width, height ):	
	if width > barcode_width_max:
		x += (width - barcode_width_max) / 2
		width = barcode_width_max
	
	barcode_widths = encode_code128( text )
	
	quiet_zone = 10
	barcode_width = sum( barcode_widths ) + quiet_zone * 2

	scale = float(width) / float(barcode_width)

	barcode_width *= scale
		
	pdf.set_fill_color( 0, 0, 0 )
	xCur = x + (width - barcode_width) / 2.0 + quiet_zone * scale
	for i, w in enumerate(barcode_widths):
		if not (i & 1):
			pdf.rect(xCur, y, w*scale, height, 'F')
		xCur += w*scale

class Rect( object ):
	AlignLeft = (1<<0)
	AlignRight = (1<<1)
	AlignCenter = (1<<2)
	AlignTop = (1<<3)
	AlignBottom = (1<<4)
	AlignMiddle = (1<<5)
	
	def __init__( self, x, y, width, height ):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		
	@property
	def top( self ): return self.y
	@property
	def bottom( self ): return self.y + self.height
	@property
	def left( self ): return self.x
	@property
	def right( self ): return self.x + self.width
	
	def contains( self, r ):
		return self.x <= r.x and r.right <= self.right and self.y <= r.y and r.bottom  <= self.bottom
		
	def align_rect( self, r, options=AlignCenter|AlignMiddle ):
		if options & self.AlignLeft:
			r.x = self.x
		elif options & self.AlignRight:
			r.x = self.right - r.width
		else:
			r.x = self.x + (self.width - r.width) / 2.0
		
		if options & self.AlignTop:
			r.y = self.y
		elif options & self.AlignBottom:
			r.y = self.bottom - r.height
		else:
			r.y = self.y + (self.height - r.height) / 2.0
	
	def draw_outline( self, pdf ):
		points = [
			(self.left, self.top),
			(self.right, self.top),
			(self.right, self.bottom),
			(self.left, self.bottom),
		]
		pLast = points[-1]
		for p in points:
			pdf.line( pLast[0], pLast[1], p[0], p[1] )
			pLast = p
	
	def x_rescale( self, factor ):
		width_new = self.width * factor
		self.x += (self.width - width_new) / 2.0
		self.width = width_new
	
	def get_rotated( self, bottomToTop=True ):
		if bottomToTop:
			return Rect( self.bottom, self.left, self.height, self.width )
		else:
			return Rect( self.top, self.right, self.height, self.width )
	
	def draw_text_to_fit( self, pdf, text, options=AlignCenter|AlignMiddle, consider_descenders=False, convert_to_text=True ):
		if convert_to_text:
			text = unicode(text).encode('windows-1252', 'ignore')
		
		descenders = has_descenders(text) if consider_descenders else False
		
		text_height = self.height * (1.0 if descenders else 1.2)
		pdf.set_font_size( text_height )
		text_width = pdf.get_string_width(text)
		
		if self.width < text_width:
			text_height *= float(self.width) / float(text_width)
			pdf.set_font_size( text_height )
			text_width = pdf.get_string_width(text)
			
		text_rect = Rect( self.x, self.y, text_width, text_height )
			
		self.align_rect( text_rect, options )
		pdf.text( text_rect.x, text_rect.y + text_height * 0.85, text )
		return text_width
	
def print_bib_tag_label( participant, sponsor_name=None, left_page=True, right_page=True, barcode=True ):
	competition = participant.competition
	license_holder = participant.license_holder
	
	bib = participant.bib
	name = u'{} {}'.format( license_holder.first_name, license_holder.last_name )
	if len(name) > 32:
		name = u'{}. {}'.format( license_holder.first_name[:1], license_holder.last_name )
	
	if sponsor_name is None:
		if competition.number_set and competition.number_set.sponsor:
			sponsor_name = competition.number_set.sponsor
		else:
			sponsor_name = competition.name
	system_name = 'CrossMgr'
	
	# Use points at the units.
	page_width = 3.9 * inches_to_points
	page_height = 2.4 * inches_to_points
	
	pdf = PDF( 'L', (page_height, page_width) )
	pdf.set_author( RaceDBVersion )
	pdf.set_title( 'Race Bib Number: {}'.format(bib) )
	pdf.set_subject( 'Bib number and rider info to be printed as a label to apply on the chip tag.' )
	pdf.set_creator( getpass.getuser() )
	pdf.set_keywords( 'RaceDB CrossMgr Bicycle Racing Software Database Road Time Trial MTB CycloCross RFID' )
	
	pdf.add_font('din1451alt', style='', fname=get_font_file('din1451alt G.ttf'), uni=True)
	pdf.add_font('Arrows', style='', fname=get_font_file('Arrrows-Regular.ttf'), uni=True)
		
	margin = min(page_height, page_width) / 18.0
	sep = margin / 2.5
	
	height = page_height - margin*2.0
	width = page_width - margin*2.0
	
	header = Rect( margin, margin, width, height / 18.0 )
	footer = Rect( margin, page_height - margin - header.height, header.width, header.height )
	field = Rect( header.x, header.bottom + sep, width, footer.top - header.bottom - sep*2 )

	license_code = license_holder.license_code
	
	leftArrow, rightArrow = 'A', 'a'
	
	font_name = 'Helvetica'
	for lp in ([True] if left_page else []) + ([False] if right_page else []):
		pdf.add_page()
		
		arrow = copy.deepcopy( header )
		arrow.y -= arrow.height * 0.5
		arrow.height *= 2
		pdf.set_font( 'Arrows' )
		arrowWidth = arrow.draw_text_to_fit( pdf, leftArrow if lp else rightArrow, (Rect.AlignLeft if lp else Rect.AlignRight)|Rect.AlignMiddle,
			consider_descenders=True,
			convert_to_text=False,
		)
		arrowWidth += pdf.get_string_width('  ')
		
		header_remain = copy.deepcopy( header )
		if lp:
			header_remain.x += arrowWidth
		header_remain.width -= arrowWidth
		
		pdf.set_font( font_name )
		header_remain.draw_text_to_fit( pdf, sponsor_name, (Rect.AlignLeft if lp else Rect.AlignRight)|Rect.AlignMiddle, True )
		
		pdf.set_font('din1451alt', '', 16)
		field.draw_text_to_fit( pdf, bib, Rect.AlignCenter|Rect.AlignMiddle )
		
		pdf.set_font( font_name )
		name_width = footer.draw_text_to_fit( pdf, name, (Rect.AlignRight if lp else Rect.AlignLeft)|Rect.AlignMiddle )
		
		logo = copy.deepcopy( footer )
		if not lp:
			logo.x += name_width + sep
		logo.width -= name_width + sep
		if logo.width > 20:
			logo_width = logo.draw_text_to_fit( pdf, system_name, (Rect.AlignLeft if lp else Rect.AlignRight)|Rect.AlignMiddle )
		else:
			logo_width = 0
		
		if barcode:
			remaining_width = min( header.width/2, header.width - name_width - logo_width )
			if lp:
				barcode_rect = Rect( footer.x + logo_width, footer.y, remaining_width, footer.height )
			else:
				barcode_rect = Rect( footer.right - logo_width - remaining_width, footer.y, remaining_width, footer.height )
			draw_code128( pdf, license_code, barcode_rect.x, barcode_rect.y, barcode_rect.width, barcode_rect.height )
		
	pdf_str = pdf.output( dest='s' )
	return pdf_str

def print_bib_on_rect( bib, license_code=None, name=None, logo=None, widthInches=5.9, heightInches=3.9, copies=1 ):
	page_width = widthInches * inches_to_points
	page_height = heightInches * inches_to_points
	
	pdf = PDF( 'L', (page_height, page_width) )
	pdf.set_author( RaceDBVersion )
	pdf.set_title( 'Race Bib Number: {}'.format(bib) )
	pdf.set_subject( 'Bib number.' )
	pdf.set_creator( getpass.getuser() )
	pdf.set_keywords( 'RaceDB CrossMgr Bicycle Racing Software Database Road Time Trial MTB CycloCross RFID' )
	pdf.add_font('din1451alt', style='', fname=get_font_file('din1451alt G.ttf'), uni=True)
		
	margin = min(page_height, page_width) / 18.0
	sep = margin / 2.5
	
	height = page_height - margin*2.0
	width = page_width - margin*2.0
	
	for c in xrange(copies):
		pdf.add_page()
		pdf.set_font('din1451alt', '', 16)
		field = Rect( margin, margin, width, height )
		field.draw_text_to_fit( pdf, bib, Rect.AlignCenter|Rect.AlignMiddle )
		
		pdf.set_font( 'Helvetica' )
		if logo:
			x = margin/2.0
			logo_rect = Rect( x, page_height-margin, (page_width - barcode_width_max)/2.0 - x, margin*0.6 )
			logo_rect.draw_text_to_fit( pdf, logo, Rect.AlignLeft|Rect.AlignMiddle )
		
		if license_code:
			barcode_rect = Rect( margin, page_height-margin, width, margin )
			draw_code128( pdf, license_code, barcode_rect.x, barcode_rect.y, barcode_rect.width, barcode_rect.height )
			
		if name:
			x = (page_width + barcode_width_max)/2.0
			name_rect = Rect( x, page_height-margin, page_width-margin/2.0 - x, margin*0.6 )
			name_rect.draw_text_to_fit( pdf, name, Rect.AlignRight|Rect.AlignMiddle )
	
	pdf_str = pdf.output( dest='s' )
	return pdf_str
	
def print_body_bib( participant ):
	license_holder = participant.license_holder
	return print_bib_on_rect(
		participant.bib,
		license_holder.license_code,
		u'{} {}'.format(license_holder.first_name, license_holder.last_name),
		'CrossMgr',
		5.9, 3.9, 2
	)
	
def print_shoulder_bib( participant ):
	license_holder = participant.license_holder
	return print_bib_on_rect(
		participant.bib,
		None,
		None,
		None,
		3.9, 2.4, 2
	)

#---------------------------------------------------------------------------------------------------------

def calculate_age( born ):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def get_nationality( participant ):
	license_holder = participant.license_holder
	nationality = license_holder.nationality
	if len(nationality) > 24:
		if license_holder.uci_country:
			nationality = license_holder.uci_country
		else:
			nationality = nationality[:24]
	if nationality == 'CANADA':
		nationality = 'Canada'
	return nationality

def format_phone( phone ):
	phone = unicode( phone )
	if len(phone) == len('AAA333NNNN') and phone.isdigit():
		return u'({}) {}-{}'.format(phone[:3], phone[3:6], phone[6:])
	return phone
	
def print_id_label( participant ):
	competition = participant.competition
	license_holder = participant.license_holder
	
	bib = participant.bib
	name = u'{} {}'.format( license_holder.first_name, license_holder.last_name )
	if len(name) > 32:
		name = u'{}. {}'.format( license_holder.first_name[:1], license_holder.last_name )
	
	system_name = 'CrossMgr'
	
	inches_to_points = 72.0
	
	# Use points at the units.
	page_width = 3.9 * inches_to_points
	page_height = 2.4 * inches_to_points
	
	pdf = PDF( 'L', (page_height, page_width) )
	pdf.set_author( RaceDBVersion )
	pdf.set_title( 'Bib Number: {}'.format(bib) )
	pdf.set_subject( 'Rider ID and Emergency Information.' )
	pdf.set_creator( getpass.getuser() )
	pdf.set_keywords( 'RaceDB CrossMgr Bicycle Racing Software Database Road Time Trial MTB CycloCross' )
	
	margin = min(page_height, page_width) / 18.0
	sep = margin / 2.5
	
	height = page_height - margin*2.0
	width = page_width - margin*2.0
	
	header = Rect( margin, margin, width, height / 10.0 )
	footer_height = height / 20
	footer = Rect( margin, page_height - margin - footer_height, header.width, footer_height )
	field = Rect( header.x, header.bottom + sep, width, footer.top - header.bottom - sep*2 )

	leftArrow, rightArrow = chr(172), chr(174)
	
	font_name = 'Helvetica'
	pdf.add_page()
	pdf.set_font( font_name, 'b' )
	
	header.draw_text_to_fit( pdf, name, Rect.AlignLeft, True )
	
	pdf.set_font( font_name )
	info = []
	info.append(
		['', u',  '.join([
			u'Age: {}'.format(calculate_age(license_holder.date_of_birth)),
			u'Date of Birth: {}'.format(license_holder.date_of_birth.strftime('%Y-%m-%d')),
			]),
		]
	)
	info.append(
		['', u',  '.join([
			u'Gender: {}'.format(license_holder.get_gender_display()),
			u'Nat: {}'.format(get_nationality(participant)),
			]),
		]
	)
	info.append( ['', ''] )
	if participant.team:
		info.append( ['', u'{}'.format(participant.team.name) ] )
	info.append(
		['', u',  '.join([
			u'Bib: {}'.format(participant.bib),
			u'Category: {}'.format(participant.category.code_gender if participant.category else ''),
			]),
		]
	)
	if license_holder.phone:
		info.append(
			['', u'  '.join([
				u'Phone: {}'.format(format_phone(license_holder.phone)),
				]),
			]
		)
	
	info.append( ['',''] )
	info.append( ['', u'Emergency Contact:'] )
	info.append( ['', u'  {}'.format(license_holder.emergency_contact_name or 'None provided')] )
	info.append( ['', u'  {}'.format(format_phone(license_holder.emergency_contact_phone or 'No phone number provided'))] )
	
	pdf.table_in_rectangle( field.x, field.y, field.width, field.height, info,
		leftJustifyCols = [0,1], hasHeader=False, horizontalLines=False )
	
	footer.draw_text_to_fit( pdf, system_name, Rect.AlignRight, True )
	
	pdf_str = pdf.output( dest='s' )
	return pdf_str
