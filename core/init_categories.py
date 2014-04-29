from django.db import transaction
from models import CategoryFormat, Category

uci_road = u'''
RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RMU	Men	Road Men Under 23
RME	Men	Road Men Elite
RMMA	Men	Road Men Masters <30-39>
RMMB	Men	Road Men Masters <40-49>
RMMC	Men	Road Men Masters <50-59>
RMMD	Men	Road Men Masters <60+>

RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWE	Women	Road Women Elite 19+
RWMA	Women	Road Women Masters <30-39>
RWMB	Women	Road Women Masters <40-49>
RWMC	Women	Road Women Masters <50+>
'''

uci_mtb = '''
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

XME	Men	MTB Men Elite
XMU	Men	MTB Men Under 23

XMMA.N	Men	MTB Novice Men Masters <30-39>
XMMA.S	Men	MTB Senior Men Masters <30-39>
XMMA.E	Men	MTB Export Men Masters <30-39>

XMMB.N	Men	MTB Novice Men Masters <40-49>
XMMB.S	Men	MTB Senior Men Masters <40-49>
XMMB.E	Men	MTB Export Men Masters <40-49>

XMMC.N	Men	MTB Novice Men Masters <50-59>
XMMC.S	Men	MTB Senior Men Masters <50-59>
XMMC.E	Men	MTB Export Men Masters <50-59>

XMMD.N	Men	MTB Novice Men Masters <60+>
XMMD.S	Men	MTB Senior Men Masters <60+>
XMMD.E	Men	MTB Export Men Masters <60+>

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
XWU	Women	MTB Women Under 23
XWE	Women	MTB Women Elite

XWMA.N	Women	MTB Novice Women Masters <30-39>
XWMA.S	Women	MTB Senior Women Masters <30-39>
XWMA.E	Women	MTB Export Women Masters <30-39>

XWMB.N	Women	MTB Novice Women Masters <40-49>
XWMB.S	Women	MTB Senior Women Masters <40-49>
XWMB.E	Women	MTB Export Women Masters <40-49>

XWMC.N	Women	MTB Novice Women Masters <50+>
XWMC.S	Women	MTB Senior Women Masters <50+>
XWMC.E	Women	MTB Export Women Masters <50+>
'''

uci_dh = '''
DMJ	Men	DH Men Junior <age 17-18>
DME	Men	DH Men Elite
DMU	Men	DH Men Under 23
DMMA	Men	DH Men Masters <30-39>
DMMB	Men	DH Men Masters <40-49>
DMMC	Men	DH Men Masters <50-59>
DMMD	Men	DH Men Masters <60+>

DWU13	Women	DH Girls Under 13 <age 10-12>
DWU15	Women	DH Girls Under 15 <age 13-14>
DWU17	Women	DH Girls Under 17 <age 15-16>
DWJ	Women	DH Women Junior <age 17-18>
DWE	Women	DH Women Elite 19+
DWMA	Women	DH Women Masters <30-39>
DWMB	Women	DH Women Masters <40-49>
DWMC	Women	DH Women Masters <50+>
'''

uci_4x = uci_dh.replace('DH', '4X').replace('DM', '4M').replace('DW', '4W')

cc_road = '''
RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RME1	Men	Road Men Elite Ability 1
RME2	Men	Road Men Elite Ability 2
RME3	Men	Road Men Elite Ability 3
RME4	Men	Road Men Elite Ability 4
RMU	Men	Road Men Under 23
RMMA	Men	Road Men Masters <30-39>
RMMB	Men	Road Men Masters <40-49>
RMMC	Men	Road Men Masters <50-59>
RMMD	Men	Road Men Masters <60+>

RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWE1	Women	Road Women Elite 19+ Ability 1
RWE2	Women	Road Women Elite 19+ Ability 2
RWE3	Women	Road Women Elite 19+ Ability 3
RWMA	Women	Road Women Masters <30-39>
RWMB	Women	Road Women Masters <40-49>
RWMC	Women	Road Women Masters <50+>
'''

usac_road = '''
RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RMC5	Men	Road Category 5
RMC4	Men	Road Category 4
RMC3	Men	Road Category 3
RMC2	Men	Road Category 2
RMC1	Men	Road Category 1

RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWC4	Women	Road Category 4
RWC3	Women	Road Category 3
RWC2	Women	Road Category 2
RWC1	Women	Road Category 1
'''

oca_road = '''
RMU13	Men	Road Boys Under 13 <age 10-12>
RMU15	Men	Road Boys Under 15 <age 13-14>
RMU17	Men	Road Boys Under 17 <age 15-16>
RMJ	Men	Road Men Junior <age 17-18>
RME.1	Men	Road Men Elite Ability 1
RME.2	Men	Road Men Elite Ability 1
RME.3	Men	Road Men Elite Ability 3
RME.4	Men	Road Men Elite Ability 4
RM.1	Men	Road Men Masters Ability 1
RM.2	Men	Road Men Masters Ability 2
RM.3	Men	Road Men Masters Ability 3

RWU13	Women	Road Girls Under 13 <age 10-12>
RWU15	Women	Road Girls Under 15 <age 13-14>
RWU17	Women	Road Girls Under 17 <age 15-16>
RWJ	Women	Road Women Junior <age 17-18>
RWE.1	Women	Road Women Elite 19+
RWE.2	Women	Road Women Elite 19+
RWMA	Women	Road Women Masters <30-39>
RWMB	Women	Road Women Masters <40-49>
RWMC	Women	Road Women Masters <50+>

MSport	Men	Road Men Sportif
WSport	Women	Road Women Sportif
'''

open = '''
Men	Men	All Men
Women	Women	All Women
'''

age = '''
MU13	Men	Boys Under 13 <age 10-12>
MU15	Men	Boys Under 15 <age 13-14>
MU17	Men	Boys Under 17 <age 15-16>
MU19	Men	Men Under 19 <age 17-18>
MU24	Men	Men Under 24 <age 19-23>
MU30	Men	Men Under 30 <age 24-29>
MU40	Men	Men Under 40 <age 30-39>
MU50	Men	Men Under 50 <age 40-49>
MU60	Men	Men Under 60 <age 50-59>
MU70	Men	Men Under 70 <age 60-69>
M_70+	Men	Men 70 and over

WU13	Women	Girls Under 13 <age 10-12>
WU15	Women	Girls Under 15 <age 13-14>
WU17	Women	Girls Under 17 <age 15-16>
WU19	Women	Women Under 19 <age 17-18>
WU24	Women	Women Under 24 <age 19-23>
WU30	Women	Women Under 30 <age 24-29>
WU40	Women	Women Under 40 <age 30-39>
WU50	Women	Women Under 50 <age 40-49>
WU60	Women	Women Under 60 <age 50-59>
WU70	Women	Women Under 70 <age 60-69>
W_70+	Women	Women 70 and over
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
]

def init_categories():
	Category.objects.all().delete()
	CategoryFormat.objects.all().delete()

	with transaction.commit_on_success():
		for (name, description, catStr) in rfs:
			print name, description
			rf = CategoryFormat( name = name + ' - Reference', description = description )
			rf.save()
			
			sequence = 0
			for cat in catStr.split( '\n' ):
				try:
					code, gender, description = cat.split( '\t' )
				except ValueError:
					continue
				print '    ', code, gender, description
				c = Category(	format = rf,
								code = code,
								gender = ['Men','Women','Open'].index(gender),
								description = description, sequence = sequence )
				c.save()
				sequence += 1

if __name__ == '__main__':
	init_categories()
