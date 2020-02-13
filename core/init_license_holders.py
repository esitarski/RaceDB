from django.db import transaction
import datetime
import string
from models import *
from large_delete_all import large_delete_all
from utils import removeDiacritic
from CountryIOC import uci_country_codes

tdf = '''
1&#x9;Chris Froome&#x9; United Kingdom&#x9;Team Sky&#x9;28&#x9;1
2&#x9;Edvald Boasson Hagen&#x9; Norway&#x9;Team Sky&#x9;26&#x9;DNS-13
3&#x9;Peter Kennaugh&#x9; United Kingdom&#x9;Team Sky&#x9;24&#x9;77
4&#x9;Vasil Kiryienka&#x9; Belarus&#x9;Team Sky&#x9;32&#x9;HD-9
5&#x9;David L&#xFFFD;pez&#x9; Spain&#x9;Team Sky&#x9;32&#x9;127
6&#x9;Richie Porte&#x9; Australia&#x9;Team Sky&#x9;28&#x9;19
7&#x9;Kanstantsin Sivtsov&#x9; Belarus&#x9;Team Sky&#x9;30&#x9;90
8&#x9;Ian Stannard&#x9; United Kingdom&#x9;Team Sky&#x9;26&#x9;135
9&#x9;Geraint Thomas&#x9; United Kingdom&#x9;Team Sky&#x9;27&#x9;140
11&#x9;Green jersey Peter Sagan&#x9; Slovakia&#x9;Cannondale&#x9;23&#x9;82
12&#x9;Maciej Bodnar&#x9; Poland&#x9;Cannondale&#x9;28&#x9;114
13&#x9;Alessandro De Marchi&#x9; Italy&#x9;Cannondale&#x9;27&#x9;71
14&#x9;Ted King&#x9; United States&#x9;Cannondale&#x9;30&#x9;HD-4
15&#x9;Kristijan Koren&#x9; Slovenia&#x9;Cannondale&#x9;26&#x9;100
16&#x9;Alan Marangoni&#x9; Italy&#x9;Cannondale&#x9;28&#x9;111
17&#x9;Moreno Moser&#x9; Italy&#x9;Cannondale&#x9;22&#x9;94
18&#x9;Fabio Sabatini&#x9; Italy&#x9;Cannondale&#x9;28&#x9;117
19&#x9;Brian Vandborg&#x9; Denmark&#x9;Cannondale&#x9;31&#x9;155
21&#x9;Jurgen Van Den Broeck&#x9; Belgium&#x9;Lotto-Belisol&#x9;30&#x9;DNS-6
22&#x9;Lars Bak&#x9; Denmark&#x9;Lotto-Belisol&#x9;33&#x9;108
23&#x9;Bart De Clercq&#x9; Belgium&#x9;Lotto-Belisol&#x9;26&#x9;38
24&#x9;Andr&#xFFFD; Greipel&#x9; Germany&#x9;Lotto-Belisol&#x9;30&#x9;129
25&#x9;Adam Hansen&#x9; Australia&#x9;Lotto-Belisol&#x9;32&#x9;72
26&#x9;Greg Henderson&#x9; New Zealand&#x9;Lotto-Belisol&#x9;36&#x9;162
27&#x9;J&#xFFFD;rgen Roelandts&#x9; Belgium&#x9;Lotto-Belisol&#x9;27&#x9;160
28&#x9;Marcel Sieberg&#x9; Germany&#x9;Lotto-Belisol&#x9;31&#x9;DNF-19
29&#x9;Frederik Willems&#x9; Belgium&#x9;Lotto-Belisol&#x9;33&#x9;163
31&#x9;Cadel Evans&#x9; Australia&#x9;BMC Racing Team&#x9;36&#x9;39
32&#x9;Brent Bookwalter&#x9; United States&#x9;BMC Racing Team&#x9;29&#x9;91
33&#x9;Marcus Burghardt&#x9; Germany&#x9;BMC Racing Team&#x9;30&#x9;98
34&#x9;Philippe Gilbert&#x9; Belgium&#x9;BMC Racing Team&#x9;30&#x9;62
35&#x9;Ama&#xFFFD;l Moinard&#x9; France&#x9;BMC Racing Team&#x9;31&#x9;56
36&#x9;Steve Morabito&#x9;  Switzerland&#x9;BMC Racing Team&#x9;30&#x9;35
37&#x9;Manuel Quinziato&#x9; Italy&#x9;BMC Racing Team&#x9;33&#x9;85
38&#x9;Michael Sch&#xFFFD;r&#x9;  Switzerland&#x9;BMC Racing Team&#x9;27&#x9;DNS-9
39&#x9;Tejay van Garderen&#x9; United States&#x9;BMC Racing Team&#x9;24&#x9;45
41&#x9;Andy Schleck&#x9; Luxembourg&#x9;RadioShack-Leopard&#x9;28&#x9;20
42&#x9;Jan Bakelants&#x9; Belgium&#x9;RadioShack-Leopard&#x9;27&#x9;18
43&#x9;Laurent Didier&#x9; Luxembourg&#x9;RadioShack-Leopard&#x9;28&#x9;53
44&#x9;Tony Gallopin&#x9; France&#x9;RadioShack-Leopard&#x9;25&#x9;58
45&#x9;Markel Irizar&#x9; Spain&#x9;RadioShack-Leopard&#x9;33&#x9;103
46&#x9;Andreas Kl&#xFFFD;den&#x9; Germany&#x9;RadioShack-Leopard&#x9;38&#x9;30
47&#x9;Maxime Monfort&#x9; Belgium&#x9;RadioShack-Leopard&#x9;30&#x9;14
48&#x9;Jens Voigt&#x9; Germany&#x9;RadioShack-Leopard&#x9;41&#x9;67
49&#x9;Haimar Zubeldia&#x9; Spain&#x9;RadioShack-Leopard&#x9;36&#x9;36
51&#x9;Pierre Rolland&#x9; France&#x9;Team Europcar&#x9;26&#x9;24
52&#x9;Yukiya Arashiro&#x9; Japan&#x9;Team Europcar&#x9;28&#x9;99
53&#x9;J&#xFFFD;r&#xFFFD;me Cousin&#x9; France&#x9;Team Europcar&#x9;24&#x9;156
54&#x9;Cyril Gautier&#x9; France&#x9;Team Europcar&#x9;25&#x9;32
55&#x9;Yohann G&#xFFFD;ne&#x9; France&#x9;Team Europcar&#x9;31&#x9;158
56&#x9;Davide Malacarne&#x9; Italy&#x9;Team Europcar&#x9;25&#x9;49
57&#x9;K&#xFFFD;vin Reza&#x9; France&#x9;Team Europcar&#x9;25&#x9;134
58&#x9;David Veilleux&#x9; Canada&#x9;Team Europcar&#x9;25&#x9;123
59&#x9;Thomas Voeckler&#x9; France&#x9;Team Europcar&#x9;34&#x9;65
61&#x9;Janez Brajkovic&#x9; Slovenia&#x9;Astana&#x9;29&#x9;DNS-7
62&#x9;Assan Bazayev&#x9; Kazakhstan&#x9;Astana&#x9;32&#x9;168
63&#x9;Jakob Fuglsang&#x9; Denmark&#x9;Astana&#x9;28&#x9;7
64&#x9;Enrico Gasparotto&#x9; Italy&#x9;Astana&#x9;31&#x9;95
65&#x9;Francesco Gavazzi&#x9; Italy&#x9;Astana&#x9;28&#x9;84
66&#x9;Andrey Kashechkin&#x9; Kazakhstan&#x9;Astana&#x9;33&#x9;DNF-3
67&#x9;Fredrik Kessiakoff&#x9; Sweden&#x9;Astana&#x9;33&#x9;DNF-6
68&#x9;Alexey Lutsenko&#x9; Kazakhstan&#x9;Astana&#x9;20&#x9;DNF-18
69&#x9;Dimitry Muravyev&#x9; Kazakhstan&#x9;Astana&#x9;33&#x9;167
71&#x9;Thibaut Pinot&#x9; France&#x9;FDJ.fr&#x9;23&#x9;DNS-16
72&#x9;William Bonnet&#x9; France&#x9;FDJ.fr&#x9;31&#x9;DNF-18
73&#x9;Nacer Bouhanni&#x9; France&#x9;FDJ.fr&#x9;22&#x9;DNF-6
74&#x9;Pierrick F&#xFFFD;drigo&#x9; France&#x9;FDJ.fr&#x9;34&#x9;59
75&#x9;Murilo Fischer&#x9; Brazil&#x9;FDJ.fr&#x9;34&#x9;133
76&#x9;Alexandre Geniez&#x9; France&#x9;FDJ.fr&#x9;25&#x9;44
77&#x9;Arnold Jeannesson&#x9; France&#x9;FDJ.fr&#x9;27&#x9;29
78&#x9;J&#xFFFD;r&#xFFFD;my Roy&#x9; France&#x9;FDJ.fr&#x9;30&#x9;126
79&#x9;Arthur Vichot&#x9; France&#x9;FDJ.fr&#x9;24&#x9;66
81&#x9;Jean-Christophe P&#xFFFD;raud&#x9; France&#x9;Ag2r-La Mondiale&#x9;36&#x9;DNF-17
82&#x9;Romain Bardet&#x9; France&#x9;Ag2r-La Mondiale&#x9;22&#x9;15
83&#x9;Maxime Bouet&#x9; France&#x9;Ag2r-La Mondiale&#x9;26&#x9;DNS-6
84&#x9;Samuel Dumoulin&#x9; France&#x9;Ag2r-La Mondiale&#x9;32&#x9;143
85&#x9;Hubert Dupont&#x9; France&#x9;Ag2r-La Mondiale&#x9;32&#x9;34
86&#x9;John Gadret&#x9; France&#x9;Ag2r-La Mondiale&#x9;34&#x9;22
87&#x9;Blel Kadri&#x9; France&#x9;Ag2r-La Mondiale&#x9;26&#x9;125
88&#x9;S&#xFFFD;bastien Minard&#x9; France&#x9;Ag2r-La Mondiale&#x9;31&#x9;124
89&#x9;Christophe Riblon&#x9; France&#x9;Ag2r-La Mondiale&#x9;32&#x9;37
91&#x9;Alberto Contador&#x9; Spain&#x9;Team Saxo-Tinkoff&#x9;30&#x9;4
92&#x9;Daniele Bennati&#x9; Italy&#x9;Team Saxo-Tinkoff&#x9;32&#x9;107
93&#x9;Jes&#xFFFD;s Hern&#xFFFD;ndez&#x9; Spain&#x9;Team Saxo-Tinkoff&#x9;31&#x9;43
94&#x9;Roman Kreuziger&#x9; Czech Republic&#x9;Team Saxo-Tinkoff&#x9;27&#x9;5
95&#x9;Benjam&#xFFFD;n Noval&#x9; Spain&#x9;Team Saxo-Tinkoff&#x9;34&#x9;DNF-9
96&#x9;S&#xFFFD;rgio Paulinho&#x9; Portugal&#x9;Team Saxo-Tinkoff&#x9;33&#x9;136
97&#x9;Nicolas Roche&#x9; Ireland&#x9;Team Saxo-Tinkoff&#x9;28&#x9;40
98&#x9;Michael Rogers&#x9; Australia&#x9;Team Saxo-Tinkoff&#x9;33&#x9;16
99&#x9;Matteo Tosatto&#x9; Italy&#x9;Team Saxo-Tinkoff&#x9;39&#x9;92
101&#x9;Joaquim Rodr&#xFFFD;guez&#x9; Spain&#x9;Team Katusha&#x9;34&#x9;3
102&#x9;Pavel Brutt&#x9; Russia&#x9;Team Katusha&#x9;31&#x9;110
103&#x9;Alexander Kristoff&#x9; Norway&#x9;Team Katusha&#x9;25&#x9;147
104&#x9;Aleksandr Kuschynski&#x9; Belarus&#x9;Team Katusha&#x9;33&#x9;141
105&#x9;Alberto Losada&#x9; Spain&#x9;Team Katusha&#x9;31&#x9;109
106&#x9;Daniel Moreno&#x9; Spain&#x9;Team Katusha&#x9;31&#x9;17
107&#x9;Gatis Smukulis&#x9; Latvia&#x9;Team Katusha&#x9;26&#x9;119
108&#x9;Yuri Trofimov&#x9; Russia&#x9;Team Katusha&#x9;29&#x9;51
109&#x9;Eduard Vorganov&#x9; Russia&#x9;Team Katusha&#x9;30&#x9;48
111&#x9;Igor Ant&#xFFFD;n&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;30&#x9;69
112&#x9;Mikel Astarloza&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;33&#x9;42
113&#x9;Gorka Izagirre&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;25&#x9;DNS-17
114&#x9;Jon Izagirre&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;24&#x9;23
115&#x9;Juan Jos&#xFFFD; Lobato&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;24&#x9;78
116&#x9;Mikel Nieve&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;29&#x9;12
117&#x9;Juan Jos&#xFFFD; Oroz&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;32&#x9;165
118&#x9;Rub&#xFFFD;n P&#xFFFD;rez&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;31&#x9;139
119&#x9;Romain Sicard&#x9; France&#x9;Euskaltel-Euskadi&#x9;25&#x9;122
121&#x9;Alejandro Valverde&#x9; Spain&#x9;Movistar Team&#x9;33&#x9;8
122&#x9;Andrey Amador&#x9; Costa Rica&#x9;Movistar Team&#x9;26&#x9;54
123&#x9;Jonathan Castroviejo&#x9; Spain&#x9;Movistar Team&#x9;26&#x9;97
124&#x9;Rui Costa&#x9; Portugal&#x9;Movistar Team&#x9;26&#x9;27
125&#x9;Imanol Erviti&#x9; Spain&#x9;Movistar Team&#x9;29&#x9;118
126&#x9;Jos&#xFFFD; Iv&#xFFFD;n Guti&#xFFFD;rrez&#x9; Spain&#x9;Movistar Team&#x9;34&#x9;DNF-9
127&#x9;Rub&#xFFFD;n Plaza&#x9; Spain&#x9;Movistar Team&#x9;33&#x9;47
128&#x9;Nairo Quintana&#x9; Colombia&#x9;Movistar Team&#x9;23&#x9;2
129&#x9;Jos&#xFFFD; Joaqu&#xFFFD;n Rojas&#x9; Spain&#x9;Movistar Team&#x9;28&#x9;79
131&#x9;Rein Taaram&#xFFFD;e&#x9; Estonia&#x9;Cofidis&#x9;26&#x9;102
132&#x9;Yoann Bagot&#x9; France&#x9;Cofidis&#x9;25&#x9;DNF-3
133&#x9;J&#xFFFD;r&#xFFFD;me Coppel&#x9; France&#x9;Cofidis&#x9;26&#x9;63
134&#x9;Egoitz Garc&#xFFFD;a&#x9; Spain&#x9;Cofidis&#x9;27&#x9;115
135&#x9;Christophe Le M&#xFFFD;vel&#x9; France&#x9;Cofidis&#x9;32&#x9;DNF-19
136&#x9;Guillaume Levarlet&#x9; France&#x9;Cofidis&#x9;27&#x9;61
137&#x9;Luis &#xFFFD;ngel Mat&#xFFFD;&#x9; Spain&#x9;Cofidis&#x9;29&#x9;88
138&#x9;Rudy Molard&#x9; France&#x9;Cofidis&#x9;23&#x9;73
139&#x9;Daniel Navarro&#x9; Spain&#x9;Cofidis&#x9;29&#x9;9
141&#x9;Damiano Cunego&#x9; Italy&#x9;Lampre-Merida&#x9;31&#x9;55
142&#x9;Matteo Bono&#x9; Italy&#x9;Lampre-Merida&#x9;29&#x9;DNF-8
143&#x9;Davide Cimolai&#x9; Italy&#x9;Lampre-Merida&#x9;23&#x9;137
144&#x9;Elia Favilli&#x9; Italy&#x9;Lampre-Merida&#x9;24&#x9;128
145&#x9;Roberto Ferrari&#x9; Italy&#x9;Lampre-Merida&#x9;30&#x9;157
146&#x9;Adriano Malori&#x9; Italy&#x9;Lampre-Merida&#x9;25&#x9;DNF-7
147&#x9;Manuele Mori&#x9; Italy&#x9;Lampre-Merida&#x9;32&#x9;76
148&#x9;Przemyslaw Niemiec&#x9; Poland&#x9;Lampre-Merida&#x9;33&#x9;57
149&#x9;Jos&#xFFFD; Serpa&#x9; Colombia&#x9;Lampre-Merida&#x9;34&#x9;21
151&#x9;Mark Cavendish&#x9; United Kingdom&#x9;Omega Pharma-Quick Step&#x9;28&#x9;148
152&#x9;Sylvain Chavanel&#x9; France&#x9;Omega Pharma-Quick Step&#x9;34&#x9;31
153&#x9;Michal Kwiatkowski&#x9; Poland&#x9;Omega Pharma-Quick Step&#x9;23&#x9;11
154&#x9;Tony Martin&#x9; Germany&#x9;Omega Pharma-Quick Step&#x9;28&#x9;106
155&#x9;J&#xFFFD;r&#xFFFD;me Pineau&#x9; France&#x9;Omega Pharma-Quick Step&#x9;33&#x9;159
156&#x9;Gert Steegmans&#x9; Belgium&#x9;Omega Pharma-Quick Step&#x9;32&#x9;153
157&#x9;Niki Terpstra&#x9; Netherlands&#x9;Omega Pharma-Quick Step&#x9;29&#x9;149
158&#x9;Matteo Trentin&#x9; Italy&#x9;Omega Pharma-Quick Step&#x9;23&#x9;142
159&#x9;Peter Velits&#x9; Slovakia&#x9;Omega Pharma-Quick Step&#x9;28&#x9;25
161&#x9;Lars Boom&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;27&#x9;105
162&#x9;Robert Gesink&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;26&#x9;26
163&#x9;Tom Leezer&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;27&#x9;150
164&#x9;Bauke Mollema&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;26&#x9;6
165&#x9;Lars Petter Nordhaug&#x9; Norway&#x9;Belkin Pro Cycling&#x9;28&#x9;50
166&#x9;Bram Tankink&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;34&#x9;64
167&#x9;Laurens ten Dam&#x9; Netherlands&#x9;Belkin Pro Cycling&#x9;32&#x9;13
168&#x9;Sep Vanmarcke&#x9; Belgium&#x9;Belkin Pro Cycling&#x9;24&#x9;131
169&#x9;Maarten Wynants&#x9; Belgium&#x9;Belkin Pro Cycling&#x9;30&#x9;132
171&#x9;Ryder Hesjedal&#x9; Canada&#x9;Garmin-Sharp&#x9;32&#x9;70
172&#x9;Jack Bauer&#x9; New Zealand&#x9;Garmin-Sharp&#x9;28&#x9;DNF-19
173&#x9;Tom Danielson&#x9; United States&#x9;Garmin-Sharp&#x9;35&#x9;60
174&#x9;Rohan Dennis&#x9; Australia&#x9;Garmin-Sharp&#x9;23&#x9;DNS-9
175&#x9;Daniel Martin&#x9; Ireland&#x9;Garmin-Sharp&#x9;26&#x9;33
176&#x9;David Millar&#x9; United Kingdom&#x9;Garmin-Sharp&#x9;36&#x9;113
177&#x9;Ramunas Navardauskas&#x9; Lithuania&#x9;Garmin-Sharp&#x9;25&#x9;120
178&#x9;Andrew Talansky&#x9; United States&#x9;Garmin-Sharp&#x9;24&#x9;10
179&#x9;Christian Vande Velde&#x9; United States&#x9;Garmin-Sharp&#x9;37&#x9;DNF-7
181&#x9;Simon Gerrans&#x9; Australia&#x9;Orica-GreenEDGE&#x9;33&#x9;80
182&#x9;Michael Albasini&#x9;  Switzerland&#x9;Orica-GreenEDGE&#x9;32&#x9;86
183&#x9;Simon Clarke&#x9; Australia&#x9;Orica-GreenEDGE&#x9;26&#x9;68
184&#x9;Matthew Goss&#x9; Australia&#x9;Orica-GreenEDGE&#x9;26&#x9;152
185&#x9;Daryl Impey&#x9; South Africa&#x9;Orica-GreenEDGE&#x9;28&#x9;74
186&#x9;Brett Lancaster&#x9; Australia&#x9;Orica-GreenEDGE&#x9;33&#x9;154
187&#x9;Cameron Meyer&#x9; Australia&#x9;Orica-GreenEDGE&#x9;25&#x9;130
188&#x9;Stuart O'Grady&#x9; Australia&#x9;Orica-GreenEDGE&#x9;39&#x9;161
189&#x9;Svein Tuft&#x9; Canada&#x9;Orica-GreenEDGE&#x9;36&#x9;169
191&#x9;John Degenkolb&#x9; Germany&#x9;Argos-Shimano&#x9;24&#x9;121
192&#x9;Roy Curvers&#x9; Netherlands&#x9;Argos-Shimano&#x9;33&#x9;145
193&#x9;Koen de Kort&#x9; Netherlands&#x9;Argos-Shimano&#x9;30&#x9;138
194&#x9;Tom Dumoulin&#x9; Netherlands&#x9;Argos-Shimano&#x9;22&#x9;41
195&#x9;Johannes Fr&#xFFFD;hlinger&#x9; Germany&#x9;Argos-Shimano&#x9;28&#x9;146
196&#x9;Simon Geschke&#x9; Germany&#x9;Argos-Shimano&#x9;27&#x9;75
197&#x9;Marcel Kittel&#x9; Germany&#x9;Argos-Shimano&#x9;25&#x9;166
198&#x9;Albert Timmer&#x9; Netherlands&#x9;Argos-Shimano&#x9;28&#x9;164
199&#x9;Tom Veelers&#x9; Netherlands&#x9;Argos-Shimano&#x9;28&#x9;DNF-19
201&#x9;Wout Poels&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;25&#x9;28
202&#x9;Kris Boeckmans&#x9; Belgium&#x9;Vacansoleil-DCM&#x9;26&#x9;DNF-19
203&#x9;Thomas De Gendt&#x9; Belgium&#x9;Vacansoleil-DCM&#x9;26&#x9;96
204&#x9;Juan Antonio Flecha&#x9; Spain&#x9;Vacansoleil-DCM&#x9;35&#x9;93
205&#x9;Johnny Hoogerland&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;30&#x9;101
206&#x9;Sergey Lagutin&#x9; Uzbekistan&#x9;Vacansoleil-DCM&#x9;32&#x9;83
207&#x9;Boy van Poppel&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;25&#x9;144
208&#x9;Danny van Poppel&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;19&#x9;DNS-16
209&#x9;Lieuwe Westra&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;30&#x9;DNF-21
211&#x9;Brice Feillu&#x9; France&#x9;Sojasun&#x9;27&#x9;104
212&#x9;Anthony Delaplace&#x9; France&#x9;Sojasun&#x9;23&#x9;89
213&#x9;Julien El Fares&#x9; France&#x9;Sojasun&#x9;28&#x9;81
214&#x9;Jonathan Hivert&#x9; France&#x9;Sojasun&#x9;28&#x9;151
215&#x9;Cyril Lemoine&#x9; France&#x9;Sojasun&#x9;30&#x9;112
216&#x9;Jean-Marc Marino&#x9; France&#x9;Sojasun&#x9;29&#x9;116
217&#x9;Maxime M&#xFFFD;derel&#x9; France&#x9;Sojasun&#x9;32&#x9;52
218&#x9;Julien Simon&#x9; France&#x9;Sojasun&#x9;27&#x9;87
219&#x9;Alexis Vuillermoz&#x9; France&#x9;Sojasun&#x9;25&#x9;46
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
			
			safe_print( first_name, last_name, gender, date_of_birth, nationality, uci_code, team )
			fields = {
				'first_name': first_name,
				'last_name': last_name,
				'gender': gender,
				'nationality': nationality,
				'date_of_birth': date_of_birth,
				'uci_code': uci_code,
				'license_code':  u'{}'.format(count+1),
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
