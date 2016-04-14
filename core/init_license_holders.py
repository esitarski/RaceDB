# coding=utf-8

from django.db import transaction
import datetime
import string
from models import *
from large_delete_all import large_delete_all
from utils import removeDiacritic
from CountryIOC import uci_country_codes

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
			nationality_code = uci_country_codes.get( nationality.upper(), 'CAN' )
			
			uci_code = nationality_code + date_of_birth.strftime( '%Y%m%d' )
			
			print removeDiacritic(first_name), removeDiacritic(last_name), \
				removeDiacritic(gender), removeDiacritic(date_of_birth), removeDiacritic(nationality), \
				removeDiacritic(uci_code), removeDiacritic(team)
			fields = {
				'first_name': first_name,
				'last_name': last_name,
				'gender': gender,
				'nationality': nationality,
				'date_of_birth': date_of_birth,
				'uci_code': uci_code,
				'license_code ':  unicode(count+1),
			}
			if not LicenseHolder.objects.filter(**fields).exists():
				LicenseHolder(**fields).save()
			
			if not Team.objects.filter(name = team).exists():
				Team(
					name = team,
					team_code = team[:3],
					team_type = 7,
				).save()
				
	process_records( lines )

if __name__ == '__main__':
	init_license_holders()
