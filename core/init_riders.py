# coding=utf-8
from django.db import transaction
import datetime
import string
from models import Rider
from large_delete_all import large_delete_all

tdf = '''
1	Alberto Contador	 Spain	Saxo Bank-SunGard	28	5
2	Jesús Hernández	 Spain	Saxo Bank-SunGard	29	92
3	Daniel Navarro	 Spain	Saxo Bank-SunGard	27	62
4	Benjamín Noval	 Spain	Saxo Bank-SunGard	32	116
5	Richie Porte	 Australia	Saxo Bank-SunGard	26	72
6	Chris Anker Sørensen	 Denmark	Saxo Bank-SunGard	26	37
7	Nicki Sørensen	 Denmark	Saxo Bank-SunGard	36	95
8	Matteo Tosatto	 Italy	Saxo Bank-SunGard	37	123
9	Brian Vandborg	 Denmark	Saxo Bank-SunGard	29	125
11	Andy Schleck	 Luxembourg	Leopard Trek	26	2
12	Fabian Cancellara	 Switzerland	Leopard Trek	30	119
13	Jakob Fuglsang	 Denmark	Leopard Trek	26	50
14	Linus Gerdemann	 Germany	Leopard Trek	28	60
15	Maxime Monfort	 Belgium	Leopard Trek	28	29
16	Stuart O'Grady	 Australia	Leopard Trek	37	78
17	Joost Posthuma	 Netherlands	Leopard Trek	30	108
18	Fränk Schleck	 Luxembourg	Leopard Trek	31	3
19	Jens Voigt	 Germany	Leopard Trek	39	67
21	 Samuel Sánchez	 Spain	Euskaltel-Euskadi	33	6
22	Gorka Izagirre	 Spain	Euskaltel-Euskadi	23*	66
23	Egoi Martínez	 Spain	Euskaltel-Euskadi	33	34
24	Alan Pérez	 Spain	Euskaltel-Euskadi	28	94
25	Rubén Pérez	 Spain	Euskaltel-Euskadi	29	75
26	Amets Txurruka	 Spain	Euskaltel-Euskadi	28	DNF-9
27	Pablo Urtasun	 Spain	Euskaltel-Euskadi	31	149
28	Iván Velasco	 Spain	Euskaltel-Euskadi	31	DNS-6
29	Gorka Verdugo	 Spain	Euskaltel-Euskadi	32	25
31	Jurgen Van Den Broeck	 Belgium	Omega Pharma-Lotto	28	DNF-9
32	Philippe Gilbert	 Belgium	Omega Pharma-Lotto	28	38
33	André Greipel	 Germany	Omega Pharma-Lotto	28	156
34	Sebastian Lang	 Germany	Omega Pharma-Lotto	31	113
35	Jurgen Roelandts	 Belgium	Omega Pharma-Lotto	26	85
36	Marcel Sieberg	 Germany	Omega Pharma-Lotto	29	141
37	Jurgen Van de Walle	 Belgium	Omega Pharma-Lotto	34	DNF-4
38	Jelle Vanendert	 Belgium	Omega Pharma-Lotto	26	20
39	Frederik Willems	 Belgium	Omega Pharma-Lotto	31	DNF-9
41	Robert Gesink	 Netherlands	Rabobank	25*	33
42	Carlos Barredo	 Spain	Rabobank	30	35
43	Lars Boom	 Netherlands	Rabobank	25	DNF-13
44	Juan Manuel Gárate	 Spain	Rabobank	35	DNS-9
45	Bauke Mollema	 Netherlands	Rabobank	24*	70
46	Grischa Niermann	 Germany	Rabobank	35	71
47	Luis León Sánchez	 Spain	Rabobank	27	57
48	Laurens ten Dam	 Netherlands	Rabobank	30	58
49	Maarten Tjallingii	 Netherlands	Rabobank	33	99
51	Thor Hushovd	 Norway	 Garmin-Cervélo	33	68
52	Tom Danielson	 United States	 Garmin-Cervélo	33	9
53	Julian Dean	 New Zealand	 Garmin-Cervélo	36	145
54	Tyler Farrar	 United States	 Garmin-Cervélo	27	159
55	Ryder Hesjedal	 Canada	 Garmin-Cervélo	30	18
56	David Millar	 United Kingdom	 Garmin-Cervélo	34	76
57	Ramunas Navardauskas	 Lithuania	 Garmin-Cervélo	23*	157
58	Christian Vande Velde	 United States	 Garmin-Cervélo	35	17
59	David Zabriskie	 United States	 Garmin-Cervélo	32	DNF-9
61	Alexandre Vinokourov	 Kazakhstan	Astana	37	DNF-9
62	Rémy Di Gregorio	 France	Astana	25	39
63	Dmitry Fofonov	 Kazakhstan	Astana	34	106
64	Andriy Hryvko	 Ukraine	Astana	27	144
65	Maxim Iglinsky	 Kazakhstan	Astana	30	105
66	Roman Kreuziger	 Czech Republic	Astana	25*	112
67	Paolo Tiralongo	 Italy	Astana	33	DNF-17
68	Tomas Vaitkus	 Lithuania	Astana	29	140
69	Andrey Zeits	 Kazakhstan	Astana	24*	45
71	Janez Brajkovic	 Slovenia	Team RadioShack	27	DNF-5
72	Chris Horner	 United States	Team RadioShack	39	DNS-8
73	Markel Irizar	 Spain	Team RadioShack	31	84
74	Andreas Klöden	 Germany	Team RadioShack	36	DNF-13
75	Levi Leipheimer	 United States	Team RadioShack	37	32
76	Dimitry Muravyev	 Kazakhstan	Team RadioShack	31	129
77	Sérgio Paulinho	 Portugal	Team RadioShack	31	81
78	Yaroslav Popovych	 Ukraine	Team RadioShack	31	DNS-10
79	Haimar Zubeldia	 Spain	Team RadioShack	34	16
81	David Arroyo	 Spain	Movistar Team	31	36
82	Andrey Amador	 Costa Rica	Movistar Team	24*	166
83	Rui Costa	 Portugal	Movistar Team	24 *	90
84	Imanol Erviti	 Spain	Movistar Team	27	88
85	Iván Gutiérrez	 Spain	Movistar Team	32	102
86	Beñat Intxausti	 Spain	Movistar Team	25*	DNF-8
87	Vasil Kiryienka	 Belarus	Movistar Team	30	HD-6
88	José Joaquin Rojas	 Spain	Movistar Team	26	80
89	Francisco Ventoso	 Spain	Movistar Team	29	139
91	Ivan Basso	 Italy	Liquigas-Cannondale	33	8
92	Maciej Bodnar	 Poland	Liquigas-Cannondale	26	143
93	Kristijan Koren	 Slovenia	Liquigas-Cannondale	24*	87
94	Paolo Longo Borghini	 Italy	Liquigas-Cannondale	30	126
95	Daniel Oss	 Italy	Liquigas-Cannondale	24*	100
96	Maciej Paterski	 Poland	Liquigas-Cannondale	24*	69
97	Fabio Sabatini	 Italy	Liquigas-Cannondale	26	167
98	Sylwester Szmyd	 Poland	Liquigas-Cannondale	33	42
99	Alessandro Vanotti	 Italy	Liquigas-Cannondale	30	133
101	Nicolas Roche	 Ireland	Ag2r-La Mondiale	26	26
102	Maxime Bouet	 France	Ag2r-La Mondiale	24*	55
103	Hubert Dupont	 France	Ag2r-La Mondiale	30	22
104	John Gadret	 France	Ag2r-La Mondiale	32	DNF-11
105	Sébastien Hinault	 France	Ag2r-La Mondiale	37	111
106	Blel Kadri	 France	Ag2r-La Mondiale	24*	117
107	Sébastien Minard	 France	Ag2r-La Mondiale	29	110
108	Jean-Christophe Péraud	 France	Ag2r-La Mondiale	34	10
109	Christophe Riblon	 France	Ag2r-La Mondiale	30	51
111	Bradley Wiggins	 United Kingdom	Team Sky	31	DNF-7
112	Juan Antonio Flecha	 Spain	Team Sky	33	98
113	Simon Gerrans	 Australia	Team Sky	31	96
114	Edvald Boasson Hagen	 Norway	Team Sky	24*	53
115	Christian Knees	 Germany	Team Sky	30	64
116	Ben Swift	 United Kingdom	Team Sky	23*	137
117	Geraint Thomas	 United Kingdom	Team Sky	25*	31
118	Rigoberto Uran	 Colombia	Team Sky	24*	24
119	Xabier Zandio	 Spain	Team Sky	34	48
121	Sylvain Chavanel	 France	Quick Step	32	61
122	Tom Boonen	 Belgium	Quick Step	30	DNF-7
123	Gerald Ciolek	 Germany	Quick Step	24*	150
124	Kevin De Weert	 Belgium	Quick Step	29	13
125	Dries Devenyns	 Belgium	Quick Step	27	46
126	Addy Engels	 Netherlands	Quick Step	34	146
127	Jérôme Pineau	 France	Quick Step	31	54
128	Gert Steegmans	 Belgium	Quick Step	30	DNS-13
129	Niki Terpstra	 Netherlands	Quick Step	27	134
131	Sandy Casar	 France	FDJ	32	27
132	William Bonnet	 France	FDJ	29	HD-14
133	Mickaël Delage	 France	FDJ	25	132
134	Arnold Jeannesson	 France	FDJ	25*	15
135	Gianni Meersman	 Belgium	FDJ	25	77
136	Rémi Pauriol	 France	FDJ	29	DNF-7
137	Anthony Roux	 France	FDJ	24*	101
138	 Jérémy Roy	 France	FDJ	28	86
139	Arthur Vichot	 France	FDJ	22*	104
141	 Cadel Evans	 Australia	BMC Racing Team	34	1
142	Brent Bookwalter	 United States	BMC Racing Team	27	114
143	Marcus Burghardt	 Germany	BMC Racing Team	28	164
144	George Hincapie	 United States	BMC Racing Team	38	56
145	Amaël Moinard	 France	BMC Racing Team	29	65
146	Steve Morabito	 Switzerland	BMC Racing Team	28	49
147	Manuel Quinziato	 Italy	BMC Racing Team	31	115
148	Ivan Santaromita	 Italy	BMC Racing Team	27	83
149	Michael Schär	 Switzerland	BMC Racing Team	24*	103
151	Rein Taaramäe	 Estonia	Cofidis	24*	12
152	Mickaël Buffaz	 France	Cofidis	32	131
153	Samuel Dumoulin	 France	Cofidis	30	162
154	Leonardo Duque	 Colombia	Cofidis	31	121
155	Julien El Fares	 France	Cofidis	26	40
156	Tony Gallopin	 France	Cofidis	23*	79
157	David Moncoutié	 France	Cofidis	36	41
158	Tristan Valentin	 France	Cofidis	29	118
159	Romain Zingle	 Belgium	Cofidis	24*	152
161	Damiano Cunego	 Italy	Lampre-ISD	29	7
162	Leonardo Bertagnolli	 Italy	Lampre-ISD	33	DNF-18
163	Grega Bole	 Slovenia	Lampre-ISD	25	127
164	Matteo Bono	 Italy	Lampre-ISD	27	93
165	Danilo Hondo	 Germany	Lampre-ISD	37	109
166	Denys Kostyuk	 Ukraine	Lampre-ISD	29	153
167	David Loosli	 Switzerland	Lampre-ISD	31	59
168	Adriano Malori	 Italy	Lampre-ISD	23*	91
169	Alessandro Petacchi	 Italy	Lampre-ISD	37	107
171	 Mark Cavendish	 United Kingdom	HTC-Highroad	26	130
172	Lars Bak	 Denmark	HTC-Highroad	31	154
173	Bernhard Eisel	 Austria	HTC-Highroad	30	161
174	Matthew Goss	 Australia	HTC-Highroad	24*	142
175	Tony Martin	 Germany	HTC-Highroad	26	44
176	Danny Pate	 United States	HTC-Highroad	32	165
177	Mark Renshaw	 Australia	HTC-Highroad	28	163
178	Tejay van Garderen	 United States	HTC-Highroad	22*	82
179	Peter Velits	 Slovakia	HTC-Highroad	26	19
181	Thomas Voeckler	 France	Team Europcar	32	4
182	Anthony Charteau	 France	Team Europcar	32	52
183	Cyril Gautier	 France	Team Europcar	23*	43
184	Yohann Gène	 France	Team Europcar	30	158
185	Vincent Jérôme	 France	Team Europcar	26	155
186	Christophe Kern	 France	Team Europcar	30	DNF-5
187	Perrig Quemeneur	 France	Team Europcar	27	151
188	 Pierre Rolland	 France	Team Europcar	24*	11
189	Sébastien Turgot	 France	Team Europcar	27	120
191	Vladimir Karpets	 Russia	Team Katusha	30	28
192	Pavel Brutt	 Russia	Team Katusha	29	DNF-9
193	Denis Galimzyanov	 Russia	Team Katusha	24*	HD-12
194	Vladimir Gusev	 Russia	Team Katusha	28	23
195	Mikhail Ignatiev	 Russia	Team Katusha	26	147
196	Vladimir Isaichev	 Russia	Team Katusha	25*	DNF-13
197	Alexandr Kolobnev	 Russia	Team Katusha	30	DNS-10
198	Egor Silin	 Russia	Team Katusha	23*	73
199	Yuri Trofimov	 Russia	Team Katusha	27	30
201	Romain Feillu	 France	Vacansoleil-DCM	27	DNS-12
202	Borut Božic	 Slovenia	Vacansoleil-DCM	30	136
203	Thomas De Gendt	 Belgium	Vacansoleil-DCM	24*	63
204	Johnny Hoogerland	 Netherlands	Vacansoleil-DCM	28	74
205	Björn Leukemans	 Belgium	Vacansoleil-DCM	34	HD-19
206	Marco Marcato	 Italy	Vacansoleil-DCM	27	89
207	Wout Poels	 Netherlands	Vacansoleil-DCM	23*	DNF-9
208	Rob Ruijgh	 Netherlands	Vacansoleil-DCM	24*	21
209	Lieuwe Westra	 Netherlands	Vacansoleil-DCM	28	128
211	Jérôme Coppel	 France	Saur-Sojasun	24*	14
212	Arnaud Coyot	 France	Saur-Sojasun	30	148
213	Anthony Delaplace	 France	Saur-Sojasun	21*	135
214	Jimmy Engoulvent	 France	Saur-Sojasun	31	160
215	Jérémie Galland	 France	Saur-Sojasun	28	138
216	Jonathan Hivert	 France	Saur-Sojasun	26	97
217	Fabrice Jeandesboz	 France	Saur-Sojasun	26	124
218	Laurent Mangel	 France	Saur-Sojasun	30	122
219	Yannick Talabardon	 France	Saur-Sojasun	29	47'''

def init_riders():
	large_delete_all( Rider )

	tdf = tdf.strip()
	lines = tdf.split( '\n' )
	with transaction.commit_on_success():
		for count, line in enumerate(lines):
			if count % 20 != 0:	# Only add every 20 riders.
				continue
			fields = line.split( '\t' )
			
			full_name = fields[1].strip()
			names = full_name.split()
			first_name = names[0]
			last_name = ' '.join( names[1:] )
				
			team = fields[3]
			gender = 0
			years_old = int(fields[4].strip('*'))
			date_of_birth = datetime.date( 2012 - years_old, 3, 3 )
			license = years_old
			
			print first_name, last_name, team, gender, date_of_birth, license
			r = Rider( first_name=unicode(first_name, 'iso-8859-1'), last_name=unicode(last_name, 'iso-8859-1'), team=unicode(team, 'iso-8859-1'), gender=gender, date_of_birth=date_of_birth, license=license )
			r.save()

