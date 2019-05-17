from django.db import transaction
from .models import *
from .large_delete_all import large_delete_all

uci_road = u'''
RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWMC	Women	Road Women Masters <50+>
RWMB	Women	Road Women Masters <40-49>
RWMA	Women	Road Women Masters <30-39>
RWE	Women	Road Women Elite 19+

RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RMMD	Men	Road Men Masters <60+>
RMMC	Men	Road Men Masters <50-59>
RMMB	Men	Road Men Masters <40-49>
RMMA	Men	Road Men Masters <30-39>
RMU	Men	Road Men Under 23
RME	Men	Road Men Elite
'''

uci_mtb = '''
XWU13.N	Women	MTB Novice Girls Under 13 <age 10-12>
XWU13.S	Women	MTB Senior Girls Under 13 <age 10-12>
XWU13.E	Women	MTB Export Girls Under 13 <age 10-12>

XWU15.N	Women	MTB Novice Girls Under 15 <age 13-14>
XWU15.S	Women	MTB Senior Girls Under 15 <age 13-14>
XWU15.E	Women	MTB Expert Girls Under 15 <age 13-14>

XWU17.N	Women	MTB Novice Girls Under 17 <age 15-16>
XWU17.S	Women	MTB Senior Girls Under 17 <age 15-16>
XWU17.E	Women	MTB Expert Girls Under 17 <age 15-16>

XWJ	Women	MTB Women Junior <age 17-18>

XWMC.N	Women	MTB Novice Women Masters <50+>
XWMC.S	Women	MTB Senior Women Masters <50+>
XWMC.E	Women	MTB Export Women Masters <50+>

XWMB.N	Women	MTB Novice Women Masters <40-49>
XWMB.S	Women	MTB Senior Women Masters <40-49>
XWMB.E	Women	MTB Export Women Masters <40-49>

XWMA.N	Women	MTB Novice Women Masters <30-39>
XWMA.S	Women	MTB Senior Women Masters <30-39>
XWMA.E	Women	MTB Export Women Masters <30-39>

XWU	Women	MTB Women Under 23
XWE	Women	MTB Women Elite

XMU13.N	Men	MTB Novice Boys Under 13 <age 10-12>
XMU13.S	Men	MTB Senior Boys Under 13 <age 10-12>
XMU13.E	Men	MTB Export Boys Under 13 <age 10-12>

XMU15.N	Men	MTB Novice Boys Under 15 <age 13-14>
XMU15.S	Men	MTB Senior Boys Under 15 <age 13-14>
XMU15.E	Men	MTB Expert Boys Under 15 <age 13-14>

XMU17.N	Men	MTB Novice Boys Under 17 <age 15-16>
XMU17.S	Men	MTB Senior Boys Under 17 <age 15-16>
XMU17.E	Men	MTB Expert Boys Under 17 <age 15-16>

XMJ.N	Men	MTB Novice Men Junior <age 17-18>
XMJ.S	Men	MTB Senior Men Junior <age 17-18>
XMJ.E	Men	MTB Expert Men Junior <age 17-18>

XMMD.N	Men	MTB Novice Men Masters <60+>
XMMD.S	Men	MTB Senior Men Masters <60+>
XMMD.E	Men	MTB Export Men Masters <60+>

XMMC.N	Men	MTB Novice Men Masters <50-59>
XMMC.S	Men	MTB Senior Men Masters <50-59>
XMMC.E	Men	MTB Export Men Masters <50-59>

XMMB.N	Men	MTB Novice Men Masters <40-49>
XMMB.S	Men	MTB Senior Men Masters <40-49>
XMMB.E	Men	MTB Export Men Masters <40-49>

XMMA.N	Men	MTB Novice Men Masters <30-39>
XMMA.S	Men	MTB Senior Men Masters <30-39>
XMMA.E	Men	MTB Export Men Masters <30-39>

XMU	Men	MTB Men Under 23
XME	Men	MTB Men Elite
'''

uci_dh = '''
DWU13	Women	DH Girls Under 13 <age 10-12>
DWU15	Women	DH Girls Under 15 <age 13-14>
DWU17	Women	DH Girls Under 17 <age 15-16>
DWJ	Women	DH Women Junior <age 17-18>
DWE	Women	DH Women Elite 19+
DWMC	Women	DH Women Masters <50+>
DWMB	Women	DH Women Masters <40-49>
DWMA	Women	DH Women Masters <30-39>

DMJ	Men	DH Men Junior <age 17-18>
DME	Men	DH Men Elite
DMU	Men	DH Men Under 23
DMMD	Men	DH Men Masters <60+>
DMMC	Men	DH Men Masters <50-59>
DMMB	Men	DH Men Masters <40-49>
DMMA	Men	DH Men Masters <30-39>
'''

uci_4x = uci_dh.replace('DH', '4X').replace('DM', '4M').replace('DW', '4W')

cc_road = '''
RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWE3	Women	Road Women Elite 19+ Ability 3
RWE2	Women	Road Women Elite 19+ Ability 2
RWE1	Women	Road Women Elite 19+ Ability 1
RWMC	Women	Road Women Masters <50+>
RWMB	Women	Road Women Masters <40-49>
RWMA	Women	Road Women Masters <30-39>

RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RME4	Men	Road Men Elite Ability 4
RME3	Men	Road Men Elite Ability 3
RME2	Men	Road Men Elite Ability 2
RME1	Men	Road Men Elite Ability 1
RMMD	Men	Road Men Masters <60+>
RMMC	Men	Road Men Masters <50-59>
RMMB	Men	Road Men Masters <40-49>
RMMA	Men	Road Men Masters <30-39>
RMU	Men	Road Men Under 23
'''

usac_road = '''
RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWCat4	Women	Road Category 4
RWCat3	Women	Road Category 3
RWCat2	Women	Road Category 2
RWCat1	Women	Road Category 1

RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RMCat5	Men	Road Category 5
RMCat4	Men	Road Category 4
RMCat3	Men	Road Category 3
RMCat2	Men	Road Category 2
RMCat1	Men	Road Category 1
'''

usac_cx = usac_road.replace('RW','CXW').replace('RM','CXM').replace('Road','CX')
usac_mtb = usac_road.replace('RW','MW').replace('RM','MM').replace('Road','MTB')

oca_road = '''
RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWE.1	Women	Road Women Elite 19+
RWE.2	Women	Road Women Elite 19+
RWMA	Women	Road Women Masters <30-39>
RWMB	Women	Road Women Masters <40-49>
RWMC	Women	Road Women Masters <50+>
WSport	Women	Road Women Sportif

RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RME.4	Men	Road Men Elite Ability 4
RME.3	Men	Road Men Elite Ability 3
RME.2	Men	Road Men Elite Ability 2
RME.1	Men	Road Men Elite Ability 1
RM.3	Men	Road Men Masters Ability 3
RM.2	Men	Road Men Masters Ability 2
RM.1	Men	Road Men Masters Ability 1
MSport	Men	Road Men Sportif
'''

open = '''
Women	Women	All Women
Men	Men	All Men
'''

age = '''
WU13	Women	Girls Under 13 <age 10-12>
WU15	Women	Girls Under 15 <age 13-14>
WU17	Women	Girls Under 17 <age 15-16>
WU19	Women	Women Under 19 <age 17-18>
W_70+	Women	Women 70 and over
WU70	Women	Women Under 70 <age 60-69>
WU60	Women	Women Under 60 <age 50-59>
WU50	Women	Women Under 50 <age 40-49>
WU40	Women	Women Under 40 <age 30-39>
WU30	Women	Women Under 30 <age 24-29>
WU24	Women	Women Under 24 <age 19-23>

MU13	Men	Boys Under 13 <age 10-12>
MU15	Men	Boys Under 15 <age 13-14>
MU17	Men	Boys Under 17 <age 15-16>
MU19	Men	Men Under 19 <age 17-18>
M_70+	Men	Men 70 and over
MU70	Men	Men Under 70 <age 60-69>
MU60	Men	Men Under 60 <age 50-59>
MU50	Men	Men Under 50 <age 40-49>
MU40	Men	Men Under 40 <age 30-39>
MU30	Men	Men Under 30 <age 24-29>
MU24	Men	Men Under 24 <age 19-23>
'''

rfs = [
	(u'Age',			u'Age Based', age),
	(u'UCI - Road',		u'Union Cycliste Internationale Road', uci_road),
	(u'UCI - MTB',		u'Union Cycliste Internationale Mountain Bike', uci_mtb),
	(u'UCI - DH',		u'Union Cycliste Internationale Downhill', uci_dh),
	(u'UCI - 4X',		u'Union Cycliste Internationale 4-Cross', uci_4x),
	(u'OCA - Road',		u'Ontario Cycling Association', oca_road),
	(u'CC - Road',		u'Canadian Cycling', cc_road),
	(u'Open',			u'Men and Women', open),
	(u'USAC - Road',	u'USA Cycling Road', usac_road),
	(u'USAC - CycloCross',	u'USA Cycling CycloCross', usac_cx),
	(u'USAC - MTB',	u'USA Cycling MTB', usac_mtb),
	(u'USAC - Track',	u'USA Cycling Tracl', usac_mtb),
]

def init_categories():
	large_delete_all( Category )
	large_delete_all( CategoryFormat )

	for (name, description, catStr) in rfs:
		safe_print( name, description )
		rf = CategoryFormat( name = name + ' - Reference', description = description )
		rf.save()
		
		sequence = 0
		with transaction.atomic():
			for cat in catStr.split( '\n' ):
				try:
					code, gender, description = cat.split( '\t' )
				except ValueError:
					continue
				safe_print( u'    ', code, gender, description )
				c = Category(	format = rf,
								code = code,
								gender = ['Men','Women','Open'].index(gender),
								description = description, sequence = sequence )
				c.save()
				sequence += 1

if __name__ == '__main__':
	init_categories()
