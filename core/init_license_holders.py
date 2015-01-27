# coding=utf-8

from django.db import transaction
import datetime
import string
from models import *
from large_delete_all import large_delete_all
from utils import removeDiacritic

tdf = '''
1	Chris Froome	 United Kingdom	Team Sky	28	1
2	Edvald Boasson Hagen	 Norway	Team Sky	26	DNS-13
3	Peter Kennaugh	 United Kingdom	Team Sky	24	77
4	Vasil Kiryienka	 Belarus	Team Sky	32	HD-9
5	David López	 Spain	Team Sky	32	127
6	Richie Porte	 Australia	Team Sky	28	19
7	Kanstantsin Sivtsov	 Belarus	Team Sky	30	90
8	Ian Stannard	 United Kingdom	Team Sky	26	135
9	Geraint Thomas	 United Kingdom	Team Sky	27	140
11	Green jersey Peter Sagan	 Slovakia	Cannondale	23	82
12	Maciej Bodnar	 Poland	Cannondale	28	114
13	Alessandro De Marchi	 Italy	Cannondale	27	71
14	Ted King	 United States	Cannondale	30	HD-4
15	Kristijan Koren	 Slovenia	Cannondale	26	100
16	Alan Marangoni	 Italy	Cannondale	28	111
17	Moreno Moser	 Italy	Cannondale	22	94
18	Fabio Sabatini	 Italy	Cannondale	28	117
19	Brian Vandborg	 Denmark	Cannondale	31	155
21	Jurgen Van Den Broeck	 Belgium	Lotto-Belisol	30	DNS-6
22	Lars Bak	 Denmark	Lotto-Belisol	33	108
23	Bart De Clercq	 Belgium	Lotto-Belisol	26	38
24	André Greipel	 Germany	Lotto-Belisol	30	129
25	Adam Hansen	 Australia	Lotto-Belisol	32	72
26	Greg Henderson	 New Zealand	Lotto-Belisol	36	162
27	Jürgen Roelandts	 Belgium	Lotto-Belisol	27	160
28	Marcel Sieberg	 Germany	Lotto-Belisol	31	DNF-19
29	Frederik Willems	 Belgium	Lotto-Belisol	33	163
31	Cadel Evans	 Australia	BMC Racing Team	36	39
32	Brent Bookwalter	 United States	BMC Racing Team	29	91
33	Marcus Burghardt	 Germany	BMC Racing Team	30	98
34	Philippe Gilbert	 Belgium	BMC Racing Team	30	62
35	Amaël Moinard	 France	BMC Racing Team	31	56
36	Steve Morabito	  Switzerland	BMC Racing Team	30	35
37	Manuel Quinziato	 Italy	BMC Racing Team	33	85
38	Michael Schär	  Switzerland	BMC Racing Team	27	DNS-9
39	Tejay van Garderen	 United States	BMC Racing Team	24	45
41	Andy Schleck	 Luxembourg	RadioShack-Leopard	28	20
42	Jan Bakelants	 Belgium	RadioShack-Leopard	27	18
43	Laurent Didier	 Luxembourg	RadioShack-Leopard	28	53
44	Tony Gallopin	 France	RadioShack-Leopard	25	58
45	Markel Irizar	 Spain	RadioShack-Leopard	33	103
46	Andreas Klöden	 Germany	RadioShack-Leopard	38	30
47	Maxime Monfort	 Belgium	RadioShack-Leopard	30	14
48	Jens Voigt	 Germany	RadioShack-Leopard	41	67
49	Haimar Zubeldia	 Spain	RadioShack-Leopard	36	36
51	Pierre Rolland	 France	Team Europcar	26	24
52	Yukiya Arashiro	 Japan	Team Europcar	28	99
53	Jérôme Cousin	 France	Team Europcar	24	156
54	Cyril Gautier	 France	Team Europcar	25	32
55	Yohann Gène	 France	Team Europcar	31	158
56	Davide Malacarne	 Italy	Team Europcar	25	49
57	Kévin Reza	 France	Team Europcar	25	134
58	David Veilleux	 Canada	Team Europcar	25	123
59	Thomas Voeckler	 France	Team Europcar	34	65
61	Janez Brajkovic	 Slovenia	Astana	29	DNS-7
62	Assan Bazayev	 Kazakhstan	Astana	32	168
63	Jakob Fuglsang	 Denmark	Astana	28	7
64	Enrico Gasparotto	 Italy	Astana	31	95
65	Francesco Gavazzi	 Italy	Astana	28	84
66	Andrey Kashechkin	 Kazakhstan	Astana	33	DNF-3
67	Fredrik Kessiakoff	 Sweden	Astana	33	DNF-6
68	Alexey Lutsenko	 Kazakhstan	Astana	20	DNF-18
69	Dimitry Muravyev	 Kazakhstan	Astana	33	167
71	Thibaut Pinot	 France	FDJ.fr	23	DNS-16
72	William Bonnet	 France	FDJ.fr	31	DNF-18
73	Nacer Bouhanni	 France	FDJ.fr	22	DNF-6
74	Pierrick Fédrigo	 France	FDJ.fr	34	59
75	Murilo Fischer	 Brazil	FDJ.fr	34	133
76	Alexandre Geniez	 France	FDJ.fr	25	44
77	Arnold Jeannesson	 France	FDJ.fr	27	29
78	Jérémy Roy	 France	FDJ.fr	30	126
79	Arthur Vichot	 France	FDJ.fr	24	66
81	Jean-Christophe Péraud	 France	Ag2r-La Mondiale	36	DNF-17
82	Romain Bardet	 France	Ag2r-La Mondiale	22	15
83	Maxime Bouet	 France	Ag2r-La Mondiale	26	DNS-6
84	Samuel Dumoulin	 France	Ag2r-La Mondiale	32	143
85	Hubert Dupont	 France	Ag2r-La Mondiale	32	34
86	John Gadret	 France	Ag2r-La Mondiale	34	22
87	Blel Kadri	 France	Ag2r-La Mondiale	26	125
88	Sébastien Minard	 France	Ag2r-La Mondiale	31	124
89	Christophe Riblon	 France	Ag2r-La Mondiale	32	37
91	Alberto Contador	 Spain	Team Saxo-Tinkoff	30	4
92	Daniele Bennati	 Italy	Team Saxo-Tinkoff	32	107
93	Jesús Hernández	 Spain	Team Saxo-Tinkoff	31	43
94	Roman Kreuziger	 Czech Republic	Team Saxo-Tinkoff	27	5
95	Benjamín Noval	 Spain	Team Saxo-Tinkoff	34	DNF-9
96	Sérgio Paulinho	 Portugal	Team Saxo-Tinkoff	33	136
97	Nicolas Roche	 Ireland	Team Saxo-Tinkoff	28	40
98	Michael Rogers	 Australia	Team Saxo-Tinkoff	33	16
99	Matteo Tosatto	 Italy	Team Saxo-Tinkoff	39	92
101	Joaquim Rodríguez	 Spain	Team Katusha	34	3
102	Pavel Brutt	 Russia	Team Katusha	31	110
103	Alexander Kristoff	 Norway	Team Katusha	25	147
104	Aleksandr Kuschynski	 Belarus	Team Katusha	33	141
105	Alberto Losada	 Spain	Team Katusha	31	109
106	Daniel Moreno	 Spain	Team Katusha	31	17
107	Gatis Smukulis	 Latvia	Team Katusha	26	119
108	Yuri Trofimov	 Russia	Team Katusha	29	51
109	Eduard Vorganov	 Russia	Team Katusha	30	48
111	Igor Antón	 Spain	Euskaltel-Euskadi	30	69
112	Mikel Astarloza	 Spain	Euskaltel-Euskadi	33	42
113	Gorka Izagirre	 Spain	Euskaltel-Euskadi	25	DNS-17
114	Jon Izagirre	 Spain	Euskaltel-Euskadi	24	23
115	Juan José Lobato	 Spain	Euskaltel-Euskadi	24	78
116	Mikel Nieve	 Spain	Euskaltel-Euskadi	29	12
117	Juan José Oroz	 Spain	Euskaltel-Euskadi	32	165
118	Rubén Pérez	 Spain	Euskaltel-Euskadi	31	139
119	Romain Sicard	 France	Euskaltel-Euskadi	25	122
121	Alejandro Valverde	 Spain	Movistar Team	33	8
122	Andrey Amador	 Costa Rica	Movistar Team	26	54
123	Jonathan Castroviejo	 Spain	Movistar Team	26	97
124	Rui Costa	 Portugal	Movistar Team	26	27
125	Imanol Erviti	 Spain	Movistar Team	29	118
126	José Iván Gutiérrez	 Spain	Movistar Team	34	DNF-9
127	Rubén Plaza	 Spain	Movistar Team	33	47
128	Nairo Quintana	 Colombia	Movistar Team	23	2
129	José Joaquín Rojas	 Spain	Movistar Team	28	79
131	Rein Taaramäe	 Estonia	Cofidis	26	102
132	Yoann Bagot	 France	Cofidis	25	DNF-3
133	Jérôme Coppel	 France	Cofidis	26	63
134	Egoitz García	 Spain	Cofidis	27	115
135	Christophe Le Mével	 France	Cofidis	32	DNF-19
136	Guillaume Levarlet	 France	Cofidis	27	61
137	Luis Ángel Maté	 Spain	Cofidis	29	88
138	Rudy Molard	 France	Cofidis	23	73
139	Daniel Navarro	 Spain	Cofidis	29	9
141	Damiano Cunego	 Italy	Lampre-Merida	31	55
142	Matteo Bono	 Italy	Lampre-Merida	29	DNF-8
143	Davide Cimolai	 Italy	Lampre-Merida	23	137
144	Elia Favilli	 Italy	Lampre-Merida	24	128
145	Roberto Ferrari	 Italy	Lampre-Merida	30	157
146	Adriano Malori	 Italy	Lampre-Merida	25	DNF-7
147	Manuele Mori	 Italy	Lampre-Merida	32	76
148	Przemyslaw Niemiec	 Poland	Lampre-Merida	33	57
149	José Serpa	 Colombia	Lampre-Merida	34	21
151	Mark Cavendish	 United Kingdom	Omega Pharma-Quick Step	28	148
152	Sylvain Chavanel	 France	Omega Pharma-Quick Step	34	31
153	Michal Kwiatkowski	 Poland	Omega Pharma-Quick Step	23	11
154	Tony Martin	 Germany	Omega Pharma-Quick Step	28	106
155	Jérôme Pineau	 France	Omega Pharma-Quick Step	33	159
156	Gert Steegmans	 Belgium	Omega Pharma-Quick Step	32	153
157	Niki Terpstra	 Netherlands	Omega Pharma-Quick Step	29	149
158	Matteo Trentin	 Italy	Omega Pharma-Quick Step	23	142
159	Peter Velits	 Slovakia	Omega Pharma-Quick Step	28	25
161	Lars Boom	 Netherlands	Belkin Pro Cycling	27	105
162	Robert Gesink	 Netherlands	Belkin Pro Cycling	26	26
163	Tom Leezer	 Netherlands	Belkin Pro Cycling	27	150
164	Bauke Mollema	 Netherlands	Belkin Pro Cycling	26	6
165	Lars Petter Nordhaug	 Norway	Belkin Pro Cycling	28	50
166	Bram Tankink	 Netherlands	Belkin Pro Cycling	34	64
167	Laurens ten Dam	 Netherlands	Belkin Pro Cycling	32	13
168	Sep Vanmarcke	 Belgium	Belkin Pro Cycling	24	131
169	Maarten Wynants	 Belgium	Belkin Pro Cycling	30	132
171	Ryder Hesjedal	 Canada	Garmin-Sharp	32	70
172	Jack Bauer	 New Zealand	Garmin-Sharp	28	DNF-19
173	Tom Danielson	 United States	Garmin-Sharp	35	60
174	Rohan Dennis	 Australia	Garmin-Sharp	23	DNS-9
175	Daniel Martin	 Ireland	Garmin-Sharp	26	33
176	David Millar	 United Kingdom	Garmin-Sharp	36	113
177	Ramunas Navardauskas	 Lithuania	Garmin-Sharp	25	120
178	Andrew Talansky	 United States	Garmin-Sharp	24	10
179	Christian Vande Velde	 United States	Garmin-Sharp	37	DNF-7
181	Simon Gerrans	 Australia	Orica-GreenEDGE	33	80
182	Michael Albasini	  Switzerland	Orica-GreenEDGE	32	86
183	Simon Clarke	 Australia	Orica-GreenEDGE	26	68
184	Matthew Goss	 Australia	Orica-GreenEDGE	26	152
185	Daryl Impey	 South Africa	Orica-GreenEDGE	28	74
186	Brett Lancaster	 Australia	Orica-GreenEDGE	33	154
187	Cameron Meyer	 Australia	Orica-GreenEDGE	25	130
188	Stuart O'Grady	 Australia	Orica-GreenEDGE	39	161
189	Svein Tuft	 Canada	Orica-GreenEDGE	36	169
191	John Degenkolb	 Germany	Argos-Shimano	24	121
192	Roy Curvers	 Netherlands	Argos-Shimano	33	145
193	Koen de Kort	 Netherlands	Argos-Shimano	30	138
194	Tom Dumoulin	 Netherlands	Argos-Shimano	22	41
195	Johannes Fröhlinger	 Germany	Argos-Shimano	28	146
196	Simon Geschke	 Germany	Argos-Shimano	27	75
197	Marcel Kittel	 Germany	Argos-Shimano	25	166
198	Albert Timmer	 Netherlands	Argos-Shimano	28	164
199	Tom Veelers	 Netherlands	Argos-Shimano	28	DNF-19
201	Wout Poels	 Netherlands	Vacansoleil-DCM	25	28
202	Kris Boeckmans	 Belgium	Vacansoleil-DCM	26	DNF-19
203	Thomas De Gendt	 Belgium	Vacansoleil-DCM	26	96
204	Juan Antonio Flecha	 Spain	Vacansoleil-DCM	35	93
205	Johnny Hoogerland	 Netherlands	Vacansoleil-DCM	30	101
206	Sergey Lagutin	 Uzbekistan	Vacansoleil-DCM	32	83
207	Boy van Poppel	 Netherlands	Vacansoleil-DCM	25	144
208	Danny van Poppel	 Netherlands	Vacansoleil-DCM	19	DNS-16
209	Lieuwe Westra	 Netherlands	Vacansoleil-DCM	30	DNF-21
211	Brice Feillu	 France	Sojasun	27	104
212	Anthony Delaplace	 France	Sojasun	23	89
213	Julien El Fares	 France	Sojasun	28	81
214	Jonathan Hivert	 France	Sojasun	28	151
215	Cyril Lemoine	 France	Sojasun	30	112
216	Jean-Marc Marino	 France	Sojasun	29	116
217	Maxime Méderel	 France	Sojasun	32	52
218	Julien Simon	 France	Sojasun	27	87
219	Alexis Vuillermoz	 France	Sojasun	25	46
'''

countryCodes = '''
Afghanistan	 AF	 AFG	004
ALA	Aland Islands	AX	 ALA	248
Albania	AL	 ALB	008
Algeria	DZ	 DZA	012
American Samoa	AS	 ASM	016
Andorra	AD	 AND	020
Angola	AO	 AGO	024
Anguilla	AI	 AIA	660
 	Antarctica	AQ	ATA	010
Antigua and Barbuda	AG	 ATG	028
Argentina	AR	 ARG	032
Armenia	AM	 ARM	051
Aruba	AW	 ABW	533
Australia	AU	 AUS	036
Austria	AT	 AUT	040
Azerbaijan	AZ	 AZE	031
Bahamas	BS	 BHS	044
Bahrain	BH	 BHR	048
Bangladesh	BD	 BGD	050
Barbados	BB	 BRB	052
Belarus	BY	 BLR	112
Belgium	BE	 BEL	056
Belize	BZ	 BLZ	084
Benin	BJ	 BEN	204
Bermuda	BM	 BMU	060
Bhutan	BT	 BTN	064
Bolivia	BO	 BOL	068
Bosnia and Herzegovina	BA	 BIH	070
Botswana	BW	 BWA	072
Bouvet Island	BV	BVT	074
Brazil	BR	 BRA	076
British Virgin Islands	VG	 VGB	092
British Indian Ocean Territory	IO	IOT	086
Brunei Darussalam	BN	 BRN	096
Bulgaria	BG	 BGR	100
Burkina Faso	BF	 BFA	854
Burundi	BI	 BDI	108
Cambodia	KH	 KHM	116
Cameroon	CM	 CMR	120
Canada	CA	 CAN	124
Cape Verde	CV	 CPV	132
Cayman Islands	KY	 CYM	136
Central African Republic	CF	 CAF	140
Chad	TD	 TCD	148
Chile	CL	 CHL	152
China	CN	 CHN	156
Hong Kong, Special Administrative Region of China	HK	 HKG	344
Macao, Special Administrative Region of China	MO	 MAC	446
Christmas Island	CX	CXR	162
Cocos (Keeling) Islands	CC	CCK	166
Colombia	CO	 COL	170
Comoros	KM	 COM	174
Congo (Brazzaville)	CG	 COG	178
Congo, Democratic Republic of the	CD	COD	180
Cook Islands	CK	 COK	184
Costa Rica	CR	 CRI	188
Côte d'Ivoire	CI	 CIV	384
Croatia	HR	 HRV	191
Cuba	CU	 CUB	192
Cyprus	CY	 CYP	196
Czech Republic	CZ	 CZE	203
Denmark	DK	 DNK	208
Djibouti	DJ	 DJI	262
Dominica	DM	 DMA	212
Dominican Republic	DO	 DOM	214
Ecuador	EC	 ECU	218
Egypt	EG	 EGY	818
El Salvador	SV	 SLV	222
Equatorial Guinea	GQ	 GNQ	226
Eritrea	ER	 ERI	232
Estonia	EE	 EST	233
Ethiopia	ET	 ETH	231
Falkland Islands (Malvinas)	FK	 FLK	238
Faroe Islands	FO	 FRO	234
Fiji	FJ	 FJI	242
Finland	FI	 FIN	246
France	FR	 FRA	250
French Guiana	GF	 GUF	254
French Polynesia	PF	 PYF	258
French Southern Territories	TF	ATF	260
Gabon	GA	 GAB	266
Gambia	GM	 GMB	270
Georgia	GE	 GEO	268
Germany	DE	 DEU	276
Ghana	GH	 GHA	288
Gibraltar	GI	 GIB	292
Greece	GR	 GRC	300
Greenland	GL	 GRL	304
Grenada	GD	 GRD	308
Guadeloupe	GP	 GLP	312
Guam	GU	 GUM	316
Guatemala	GT	 GTM	320
Guernsey	GG	GGY	831
Guinea	GN	 GIN	324
Guinea-Bissau	GW	 GNB	624
Guyana	GY	 GUY	328
Haiti	HT	 HTI	332
Heard Island and Mcdonald Islands	HM	HMD	334
Holy See (Vatican City State)	VA	 VAT	336
Honduras	HN	 HND	340
Hungary	HU	 HUN	348
Iceland	IS	 ISL	352
India	IN	 IND	356
Indonesia	ID	 IDN	360
Iran, Islamic Republic of	IR	 IRN	364
Iraq	IQ	 IRQ	368
Ireland	IE	 IRL	372
Isle of Man	IM	 IMN	833
Israel	IL	 ISR	376
Italy	IT	 ITA	380
Jamaica	JM	 JAM	388
Japan	JP	 JPN	392
Jersey	JE	JEY	832
Jordan	JO	 JOR	400
Kazakhstan	KZ	 KAZ	398
Kenya	KE	 KEN	404
Kiribati	KI	 KIR	296
Korea, Democratic People's Republic of	KP	PRK	408
Korea, Republic of	KR	KOR	410
Kuwait	KW	 KWT	414
Kyrgyzstan	KG	 KGZ	417
Lao PDR	LA	 LAO	418
Latvia	LV	 LVA	428
Lebanon	LB	 LBN	422
Lesotho	LS	 LSO	426
Liberia	LR	 LBR	430
Libya	LY	 LBY	434
Liechtenstein	LI	 LIE	438
Lithuania	LT	 LTU	440
Luxembourg	LU	 LUX	442
Macedonia, Republic of	MK	MKD	807
Madagascar	MG	 MDG	450
Malawi	MW	 MWI	454
Malaysia	MY	 MYS	458
Maldives	MV	 MDV	462
Mali	ML	 MLI	466
Malta	MT	 MLT	470
Marshall Islands	MH	 MHL	584
Martinique	MQ	 MTQ	474
Mauritania	MR	 MRT	478
Mauritius	MU	 MUS	480
Mayotte	YT	MYT	175
Mexico	MX	 MEX	484
Micronesia, Federated States of	FM	 FSM	583
Moldova	MD	MDA	498
Monaco	MC	 MCO	492
Mongolia	MN	 MNG	496
Montenegro	ME	MNE	499
Montserrat	MS	 MSR	500
Morocco	MA	 MAR	504
Mozambique	MZ	 MOZ	508
Myanmar	MM	 MMR	104
Namibia	NA	 NAM	516
Nauru	NR	 NRU	520
Nepal	NP	 NPL	524
Netherlands	NL	 NLD	528
Netherlands Antilles	AN	 ANT	530
New Caledonia	NC	 NCL	540
New Zealand	NZ	 NZL	554
Nicaragua	NI	 NIC	558
Niger	NE	 NER	562
Nigeria	NG	 NGA	566
Niue	NU	 NIU	570
Norfolk Island	NF	 NFK	574
Northern Mariana Islands	MP	 MNP	580
Norway	NO	 NOR	578
Oman	OM	 OMN	512
Pakistan	PK	 PAK	586
Palau	PW	 PLW	585
Palestinian Territory, Occupied	PS	 PSE	275
Panama	PA	 PAN	591
Papua New Guinea	PG	 PNG	598
Paraguay	PY	 PRY	600
Peru	PE	 PER	604
Philippines	PH	 PHL	608
Pitcairn	PN	 PCN	612
Poland	PL	 POL	616
Portugal	PT	 PRT	620Igor
Puerto Rico	PR	 PRI	630
Qatar	QA	 QAT	634
Réunion	RE	 REU	638
Romania	RO	 ROU	642
Russian Federation	RU	 RUS	643
Rwanda	RW	 RWA	646
Saint-Barthélemy	BL	BLM	652
Saint Helena	SH	 SHN	654
Saint Kitts and Nevis	KN	 KNA	659
Saint Lucia	LC	 LCA	662
Saint-Martin (French part)	MF	MAF	663
Saint Pierre and Miquelon	PM	 SPM	666
Saint Vincent and Grenadines	VC	 VCT	670
Samoa	WS	 WSM	882
San Marino	SM	 SMR	674
Sao Tome and Principe	ST	 STP	678
Saudi Arabia	SA	 SAU	682
Senegal	SN	 SEN	686
Serbia	RS	SRB	688
Seychelles	SC	 SYC	690
Sierra Leone	SL	 SLE	694
Singapore	SG	 SGP	702
Slovakia	SK	 SVK	703
Slovenia	SI	 SVN	705
Solomon Islands	SB	 SLB	090
Somalia	SO	 SOM	706
South Africa	ZA	 ZAF	710
South Georgia and the South Sandwich Islands	GS	SGS	239
South Sudan	SS	SSD	728
Spain	ES	 ESP	724
Sri Lanka	LK	 LKA	144
Sudan	SD	 SDN	736
Suriname *	SR	 SUR	740
Svalbard and Jan Mayen Islands	SJ	 SJM	744
Swaziland	SZ	 SWZ	748
Sweden	SE	 SWE	752
Switzerland	CH	 CHE	756
Syrian Arab Republic (Syria)	SY	 SYR	760
Taiwan, Republic of China	TW	TWN	158
Tajikistan	TJ	 TJK	762
Tanzania *, United Republic of	TZ	TZA	834
Thailand	TH	 THA	764
Timor-Leste	TL	 TLS	626
Togo	TG	 TGO	768
Tokelau	TK	 TKL	772
Tonga	TO	 TON	776
Trinidad and Tobago	TT	 TTO	780
Tunisia	TN	 TUN	788
Turkey	TR	 TUR	792
Turkmenistan	TM	 TKM	795
Turks and Caicos Islands	TC	 TCA	796
Tuvalu	TV	 TUV	798
Uganda	UG	 UGA	800
Ukraine	UA	 UKR	804
United Arab Emirates	AE	 ARE	784
United Kingdom	GB	 GBR	826
United States of America	US	 USA	840
United States	US	 USA	840
United States Minor Outlying Islands	UM	UMI	581
Uruguay	UY	 URY	858
Uzbekistan	UZ	 UZB	860
Vanuatu	VU	 VUT	548
Venezuela (Bolivarian Republic of)	VE	 VEN	862
Viet Nam	VN	 VNM	704
Virgin Islands, US	VI	VIR	850
Wallis and Futuna Islands	WF	 WLF	876
Western Sahara	EH	 ESH	732
Yemen	YE	 YEM	887
Zambia	ZM	 ZMB	894
Zimbabwe	ZW	 ZWE	716
'''

countryCodes = countryCodes.decode('iso-8859-1').strip()
codeForCountry = {}
for c in countryCodes.split( '\n' ):
	fields = [f.strip() for f in c.split( '\t' )]
	codeForCountry[fields[0].lower()] = fields[2]

def init_license_holders():
	global tdf
	
	large_delete_all( LicenseHolder )
	large_delete_all( Team )

	tdf = tdf.decode('iso-8859-1').strip()
	lines = tdf.split( '\n' )
	
	@transaction.atomic
	def process_records( lines ):
		for count, line in enumerate(lines):
			fields = line.split( '\t' )
			
			full_name = fields[1].strip()
			names = full_name.split()
			first_name = names[0]
			last_name = ' '.join( names[1:] )
				
			team = fields[3].strip()
			gender = 0
			years_old = int(fields[4].strip('*'))
			date_of_birth = datetime.date( 2013 - years_old, 3, 3 )
			
			nationality = fields[2].strip()
			nationality_code = codeForCountry.get( nationality.lower(), nationality[:3] ).upper()
			
			uci_code = nationality_code + date_of_birth.strftime( '%Y%m%d' )
			
			print removeDiacritic(first_name), removeDiacritic(last_name), \
				removeDiacritic(gender), removeDiacritic(date_of_birth), removeDiacritic(nationality), \
				removeDiacritic(uci_code), removeDiacritic(team)
			r = LicenseHolder(
							first_name=first_name,
							last_name=last_name,
							gender=gender,
							nationality=nationality,
							date_of_birth=date_of_birth,
							uci_code=uci_code,
							license_code = unicode(count+1) )
			r.save()
			
			if not Team.objects.filter(name = team).exists():
				t = Team(
						name = team,
						team_code = team[:3],
						team_type = 7,
					)
				t.save()
				
	process_records( lines )

if __name__ == '__main__':
	init_license_holders()
