from django.db import transaction
import datetime

from .models import *
from . import utils
from .large_delete_all import large_delete_all

tdf = '''
1&#x9;Alberto Contador&#x9; Spain&#x9;Saxo Bank-SunGard&#x9;28&#x9;5
2&#x9;Jes&#xFFFD;s Hern&#xFFFD;ndez&#x9; Spain&#x9;Saxo Bank-SunGard&#x9;29&#x9;92
3&#x9;Daniel Navarro&#x9; Spain&#x9;Saxo Bank-SunGard&#x9;27&#x9;62
4&#x9;Benjam&#xFFFD;n Noval&#x9; Spain&#x9;Saxo Bank-SunGard&#x9;32&#x9;116
5&#x9;Richie Porte&#x9; Australia&#x9;Saxo Bank-SunGard&#x9;26&#x9;72
6&#x9;Chris Anker S&#xFFFD;rensen&#x9; Denmark&#x9;Saxo Bank-SunGard&#x9;26&#x9;37
7&#x9;Nicki S&#xFFFD;rensen&#x9; Denmark&#x9;Saxo Bank-SunGard&#x9;36&#x9;95
8&#x9;Matteo Tosatto&#x9; Italy&#x9;Saxo Bank-SunGard&#x9;37&#x9;123
9&#x9;Brian Vandborg&#x9; Denmark&#x9;Saxo Bank-SunGard&#x9;29&#x9;125
11&#x9;Andy Schleck&#x9; Luxembourg&#x9;Leopard Trek&#x9;26&#x9;2
12&#x9;Fabian Cancellara&#x9; Switzerland&#x9;Leopard Trek&#x9;30&#x9;119
13&#x9;Jakob Fuglsang&#x9; Denmark&#x9;Leopard Trek&#x9;26&#x9;50
14&#x9;Linus Gerdemann&#x9; Germany&#x9;Leopard Trek&#x9;28&#x9;60
15&#x9;Maxime Monfort&#x9; Belgium&#x9;Leopard Trek&#x9;28&#x9;29
16&#x9;Stuart O'Grady&#x9; Australia&#x9;Leopard Trek&#x9;37&#x9;78
17&#x9;Joost Posthuma&#x9; Netherlands&#x9;Leopard Trek&#x9;30&#x9;108
18&#x9;Fr&#xFFFD;nk Schleck&#x9; Luxembourg&#x9;Leopard Trek&#x9;31&#x9;3
19&#x9;Jens Voigt&#x9; Germany&#x9;Leopard Trek&#x9;39&#x9;67
21&#x9; Samuel S&#xFFFD;nchez&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;33&#x9;6
22&#x9;Gorka Izagirre&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;23*&#x9;66
23&#x9;Egoi Mart&#xFFFD;nez&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;33&#x9;34
24&#x9;Alan P&#xFFFD;rez&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;28&#x9;94
25&#x9;Rub&#xFFFD;n P&#xFFFD;rez&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;29&#x9;75
26&#x9;Amets Txurruka&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;28&#x9;DNF-9
27&#x9;Pablo Urtasun&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;31&#x9;149
28&#x9;Iv&#xFFFD;n Velasco&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;31&#x9;DNS-6
29&#x9;Gorka Verdugo&#x9; Spain&#x9;Euskaltel-Euskadi&#x9;32&#x9;25
31&#x9;Jurgen Van Den Broeck&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;28&#x9;DNF-9
32&#x9;Philippe Gilbert&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;28&#x9;38
33&#x9;Andr&#xFFFD; Greipel&#x9; Germany&#x9;Omega Pharma-Lotto&#x9;28&#x9;156
34&#x9;Sebastian Lang&#x9; Germany&#x9;Omega Pharma-Lotto&#x9;31&#x9;113
35&#x9;Jurgen Roelandts&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;26&#x9;85
36&#x9;Marcel Sieberg&#x9; Germany&#x9;Omega Pharma-Lotto&#x9;29&#x9;141
37&#x9;Jurgen Van de Walle&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;34&#x9;DNF-4
38&#x9;Jelle Vanendert&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;26&#x9;20
39&#x9;Frederik Willems&#x9; Belgium&#x9;Omega Pharma-Lotto&#x9;31&#x9;DNF-9
41&#x9;Robert Gesink&#x9; Netherlands&#x9;Rabobank&#x9;25*&#x9;33
42&#x9;Carlos Barredo&#x9; Spain&#x9;Rabobank&#x9;30&#x9;35
43&#x9;Lars Boom&#x9; Netherlands&#x9;Rabobank&#x9;25&#x9;DNF-13
44&#x9;Juan Manuel G&#xFFFD;rate&#x9; Spain&#x9;Rabobank&#x9;35&#x9;DNS-9
45&#x9;Bauke Mollema&#x9; Netherlands&#x9;Rabobank&#x9;24*&#x9;70
46&#x9;Grischa Niermann&#x9; Germany&#x9;Rabobank&#x9;35&#x9;71
47&#x9;Luis Le&#xFFFD;n S&#xFFFD;nchez&#x9; Spain&#x9;Rabobank&#x9;27&#x9;57
48&#x9;Laurens ten Dam&#x9; Netherlands&#x9;Rabobank&#x9;30&#x9;58
49&#x9;Maarten Tjallingii&#x9; Netherlands&#x9;Rabobank&#x9;33&#x9;99
51&#x9;Thor Hushovd&#x9; Norway&#x9; Garmin-Cerv&#xFFFD;lo&#x9;33&#x9;68
52&#x9;Tom Danielson&#x9; United States&#x9; Garmin-Cerv&#xFFFD;lo&#x9;33&#x9;9
53&#x9;Julian Dean&#x9; New Zealand&#x9; Garmin-Cerv&#xFFFD;lo&#x9;36&#x9;145
54&#x9;Tyler Farrar&#x9; United States&#x9; Garmin-Cerv&#xFFFD;lo&#x9;27&#x9;159
55&#x9;Ryder Hesjedal&#x9; Canada&#x9; Garmin-Cerv&#xFFFD;lo&#x9;30&#x9;18
56&#x9;David Millar&#x9; United Kingdom&#x9; Garmin-Cerv&#xFFFD;lo&#x9;34&#x9;76
57&#x9;Ramunas Navardauskas&#x9; Lithuania&#x9; Garmin-Cerv&#xFFFD;lo&#x9;23*&#x9;157
58&#x9;Christian Vande Velde&#x9; United States&#x9; Garmin-Cerv&#xFFFD;lo&#x9;35&#x9;17
59&#x9;David Zabriskie&#x9; United States&#x9; Garmin-Cerv&#xFFFD;lo&#x9;32&#x9;DNF-9
61&#x9;Alexandre Vinokourov&#x9; Kazakhstan&#x9;Astana&#x9;37&#x9;DNF-9
62&#x9;R&#xFFFD;my Di Gregorio&#x9; France&#x9;Astana&#x9;25&#x9;39
63&#x9;Dmitry Fofonov&#x9; Kazakhstan&#x9;Astana&#x9;34&#x9;106
64&#x9;Andriy Hryvko&#x9; Ukraine&#x9;Astana&#x9;27&#x9;144
65&#x9;Maxim Iglinsky&#x9; Kazakhstan&#x9;Astana&#x9;30&#x9;105
66&#x9;Roman Kreuziger&#x9; Czech Republic&#x9;Astana&#x9;25*&#x9;112
67&#x9;Paolo Tiralongo&#x9; Italy&#x9;Astana&#x9;33&#x9;DNF-17
68&#x9;Tomas Vaitkus&#x9; Lithuania&#x9;Astana&#x9;29&#x9;140
69&#x9;Andrey Zeits&#x9; Kazakhstan&#x9;Astana&#x9;24*&#x9;45
71&#x9;Janez Brajkovic&#x9; Slovenia&#x9;Team RadioShack&#x9;27&#x9;DNF-5
72&#x9;Chris Horner&#x9; United States&#x9;Team RadioShack&#x9;39&#x9;DNS-8
73&#x9;Markel Irizar&#x9; Spain&#x9;Team RadioShack&#x9;31&#x9;84
74&#x9;Andreas Kl&#xFFFD;den&#x9; Germany&#x9;Team RadioShack&#x9;36&#x9;DNF-13
75&#x9;Levi Leipheimer&#x9; United States&#x9;Team RadioShack&#x9;37&#x9;32
76&#x9;Dimitry Muravyev&#x9; Kazakhstan&#x9;Team RadioShack&#x9;31&#x9;129
77&#x9;S&#xFFFD;rgio Paulinho&#x9; Portugal&#x9;Team RadioShack&#x9;31&#x9;81
78&#x9;Yaroslav Popovych&#x9; Ukraine&#x9;Team RadioShack&#x9;31&#x9;DNS-10
79&#x9;Haimar Zubeldia&#x9; Spain&#x9;Team RadioShack&#x9;34&#x9;16
81&#x9;David Arroyo&#x9; Spain&#x9;Movistar Team&#x9;31&#x9;36
82&#x9;Andrey Amador&#x9; Costa Rica&#x9;Movistar Team&#x9;24*&#x9;166
83&#x9;Rui Costa&#x9; Portugal&#x9;Movistar Team&#x9;24 *&#x9;90
84&#x9;Imanol Erviti&#x9; Spain&#x9;Movistar Team&#x9;27&#x9;88
85&#x9;Iv&#xFFFD;n Guti&#xFFFD;rrez&#x9; Spain&#x9;Movistar Team&#x9;32&#x9;102
86&#x9;Be&#xFFFD;at Intxausti&#x9; Spain&#x9;Movistar Team&#x9;25*&#x9;DNF-8
87&#x9;Vasil Kiryienka&#x9; Belarus&#x9;Movistar Team&#x9;30&#x9;HD-6
88&#x9;Jos&#xFFFD; Joaquin Rojas&#x9; Spain&#x9;Movistar Team&#x9;26&#x9;80
89&#x9;Francisco Ventoso&#x9; Spain&#x9;Movistar Team&#x9;29&#x9;139
91&#x9;Ivan Basso&#x9; Italy&#x9;Liquigas-Cannondale&#x9;33&#x9;8
92&#x9;Maciej Bodnar&#x9; Poland&#x9;Liquigas-Cannondale&#x9;26&#x9;143
93&#x9;Kristijan Koren&#x9; Slovenia&#x9;Liquigas-Cannondale&#x9;24*&#x9;87
94&#x9;Paolo Longo Borghini&#x9; Italy&#x9;Liquigas-Cannondale&#x9;30&#x9;126
95&#x9;Daniel Oss&#x9; Italy&#x9;Liquigas-Cannondale&#x9;24*&#x9;100
96&#x9;Maciej Paterski&#x9; Poland&#x9;Liquigas-Cannondale&#x9;24*&#x9;69
97&#x9;Fabio Sabatini&#x9; Italy&#x9;Liquigas-Cannondale&#x9;26&#x9;167
98&#x9;Sylwester Szmyd&#x9; Poland&#x9;Liquigas-Cannondale&#x9;33&#x9;42
99&#x9;Alessandro Vanotti&#x9; Italy&#x9;Liquigas-Cannondale&#x9;30&#x9;133
101&#x9;Nicolas Roche&#x9; Ireland&#x9;Ag2r-La Mondiale&#x9;26&#x9;26
102&#x9;Maxime Bouet&#x9; France&#x9;Ag2r-La Mondiale&#x9;24*&#x9;55
103&#x9;Hubert Dupont&#x9; France&#x9;Ag2r-La Mondiale&#x9;30&#x9;22
104&#x9;John Gadret&#x9; France&#x9;Ag2r-La Mondiale&#x9;32&#x9;DNF-11
105&#x9;S&#xFFFD;bastien Hinault&#x9; France&#x9;Ag2r-La Mondiale&#x9;37&#x9;111
106&#x9;Blel Kadri&#x9; France&#x9;Ag2r-La Mondiale&#x9;24*&#x9;117
107&#x9;S&#xFFFD;bastien Minard&#x9; France&#x9;Ag2r-La Mondiale&#x9;29&#x9;110
108&#x9;Jean-Christophe P&#xFFFD;raud&#x9; France&#x9;Ag2r-La Mondiale&#x9;34&#x9;10
109&#x9;Christophe Riblon&#x9; France&#x9;Ag2r-La Mondiale&#x9;30&#x9;51
111&#x9;Bradley Wiggins&#x9; United Kingdom&#x9;Team Sky&#x9;31&#x9;DNF-7
112&#x9;Juan Antonio Flecha&#x9; Spain&#x9;Team Sky&#x9;33&#x9;98
113&#x9;Simon Gerrans&#x9; Australia&#x9;Team Sky&#x9;31&#x9;96
114&#x9;Edvald Boasson Hagen&#x9; Norway&#x9;Team Sky&#x9;24*&#x9;53
115&#x9;Christian Knees&#x9; Germany&#x9;Team Sky&#x9;30&#x9;64
116&#x9;Ben Swift&#x9; United Kingdom&#x9;Team Sky&#x9;23*&#x9;137
117&#x9;Geraint Thomas&#x9; United Kingdom&#x9;Team Sky&#x9;25*&#x9;31
118&#x9;Rigoberto Uran&#x9; Colombia&#x9;Team Sky&#x9;24*&#x9;24
119&#x9;Xabier Zandio&#x9; Spain&#x9;Team Sky&#x9;34&#x9;48
121&#x9;Sylvain Chavanel&#x9; France&#x9;Quick Step&#x9;32&#x9;61
122&#x9;Tom Boonen&#x9; Belgium&#x9;Quick Step&#x9;30&#x9;DNF-7
123&#x9;Gerald Ciolek&#x9; Germany&#x9;Quick Step&#x9;24*&#x9;150
124&#x9;Kevin De Weert&#x9; Belgium&#x9;Quick Step&#x9;29&#x9;13
125&#x9;Dries Devenyns&#x9; Belgium&#x9;Quick Step&#x9;27&#x9;46
126&#x9;Addy Engels&#x9; Netherlands&#x9;Quick Step&#x9;34&#x9;146
127&#x9;J&#xFFFD;r&#xFFFD;me Pineau&#x9; France&#x9;Quick Step&#x9;31&#x9;54
128&#x9;Gert Steegmans&#x9; Belgium&#x9;Quick Step&#x9;30&#x9;DNS-13
129&#x9;Niki Terpstra&#x9; Netherlands&#x9;Quick Step&#x9;27&#x9;134
131&#x9;Sandy Casar&#x9; France&#x9;FDJ&#x9;32&#x9;27
132&#x9;William Bonnet&#x9; France&#x9;FDJ&#x9;29&#x9;HD-14
133&#x9;Micka&#xFFFD;l Delage&#x9; France&#x9;FDJ&#x9;25&#x9;132
134&#x9;Arnold Jeannesson&#x9; France&#x9;FDJ&#x9;25*&#x9;15
135&#x9;Gianni Meersman&#x9; Belgium&#x9;FDJ&#x9;25&#x9;77
136&#x9;R&#xFFFD;mi Pauriol&#x9; France&#x9;FDJ&#x9;29&#x9;DNF-7
137&#x9;Anthony Roux&#x9; France&#x9;FDJ&#x9;24*&#x9;101
138&#x9; J&#xFFFD;r&#xFFFD;my Roy&#x9; France&#x9;FDJ&#x9;28&#x9;86
139&#x9;Arthur Vichot&#x9; France&#x9;FDJ&#x9;22*&#x9;104
141&#x9; Cadel Evans&#x9; Australia&#x9;BMC Racing Team&#x9;34&#x9;1
142&#x9;Brent Bookwalter&#x9; United States&#x9;BMC Racing Team&#x9;27&#x9;114
143&#x9;Marcus Burghardt&#x9; Germany&#x9;BMC Racing Team&#x9;28&#x9;164
144&#x9;George Hincapie&#x9; United States&#x9;BMC Racing Team&#x9;38&#x9;56
145&#x9;Ama&#xFFFD;l Moinard&#x9; France&#x9;BMC Racing Team&#x9;29&#x9;65
146&#x9;Steve Morabito&#x9; Switzerland&#x9;BMC Racing Team&#x9;28&#x9;49
147&#x9;Manuel Quinziato&#x9; Italy&#x9;BMC Racing Team&#x9;31&#x9;115
148&#x9;Ivan Santaromita&#x9; Italy&#x9;BMC Racing Team&#x9;27&#x9;83
149&#x9;Michael Sch&#xFFFD;r&#x9; Switzerland&#x9;BMC Racing Team&#x9;24*&#x9;103
151&#x9;Rein Taaram&#xFFFD;e&#x9; Estonia&#x9;Cofidis&#x9;24*&#x9;12
152&#x9;Micka&#xFFFD;l Buffaz&#x9; France&#x9;Cofidis&#x9;32&#x9;131
153&#x9;Samuel Dumoulin&#x9; France&#x9;Cofidis&#x9;30&#x9;162
154&#x9;Leonardo Duque&#x9; Colombia&#x9;Cofidis&#x9;31&#x9;121
155&#x9;Julien El Fares&#x9; France&#x9;Cofidis&#x9;26&#x9;40
156&#x9;Tony Gallopin&#x9; France&#x9;Cofidis&#x9;23*&#x9;79
157&#x9;David Moncouti&#xFFFD;&#x9; France&#x9;Cofidis&#x9;36&#x9;41
158&#x9;Tristan Valentin&#x9; France&#x9;Cofidis&#x9;29&#x9;118
159&#x9;Romain Zingle&#x9; Belgium&#x9;Cofidis&#x9;24*&#x9;152
161&#x9;Damiano Cunego&#x9; Italy&#x9;Lampre-ISD&#x9;29&#x9;7
162&#x9;Leonardo Bertagnolli&#x9; Italy&#x9;Lampre-ISD&#x9;33&#x9;DNF-18
163&#x9;Grega Bole&#x9; Slovenia&#x9;Lampre-ISD&#x9;25&#x9;127
164&#x9;Matteo Bono&#x9; Italy&#x9;Lampre-ISD&#x9;27&#x9;93
165&#x9;Danilo Hondo&#x9; Germany&#x9;Lampre-ISD&#x9;37&#x9;109
166&#x9;Denys Kostyuk&#x9; Ukraine&#x9;Lampre-ISD&#x9;29&#x9;153
167&#x9;David Loosli&#x9; Switzerland&#x9;Lampre-ISD&#x9;31&#x9;59
168&#x9;Adriano Malori&#x9; Italy&#x9;Lampre-ISD&#x9;23*&#x9;91
169&#x9;Alessandro Petacchi&#x9; Italy&#x9;Lampre-ISD&#x9;37&#x9;107
171&#x9; Mark Cavendish&#x9; United Kingdom&#x9;HTC-Highroad&#x9;26&#x9;130
172&#x9;Lars Bak&#x9; Denmark&#x9;HTC-Highroad&#x9;31&#x9;154
173&#x9;Bernhard Eisel&#x9; Austria&#x9;HTC-Highroad&#x9;30&#x9;161
174&#x9;Matthew Goss&#x9; Australia&#x9;HTC-Highroad&#x9;24*&#x9;142
175&#x9;Tony Martin&#x9; Germany&#x9;HTC-Highroad&#x9;26&#x9;44
176&#x9;Danny Pate&#x9; United States&#x9;HTC-Highroad&#x9;32&#x9;165
177&#x9;Mark Renshaw&#x9; Australia&#x9;HTC-Highroad&#x9;28&#x9;163
178&#x9;Tejay van Garderen&#x9; United States&#x9;HTC-Highroad&#x9;22*&#x9;82
179&#x9;Peter Velits&#x9; Slovakia&#x9;HTC-Highroad&#x9;26&#x9;19
181&#x9;Thomas Voeckler&#x9; France&#x9;Team Europcar&#x9;32&#x9;4
182&#x9;Anthony Charteau&#x9; France&#x9;Team Europcar&#x9;32&#x9;52
183&#x9;Cyril Gautier&#x9; France&#x9;Team Europcar&#x9;23*&#x9;43
184&#x9;Yohann G&#xFFFD;ne&#x9; France&#x9;Team Europcar&#x9;30&#x9;158
185&#x9;Vincent J&#xFFFD;r&#xFFFD;me&#x9; France&#x9;Team Europcar&#x9;26&#x9;155
186&#x9;Christophe Kern&#x9; France&#x9;Team Europcar&#x9;30&#x9;DNF-5
187&#x9;Perrig Quemeneur&#x9; France&#x9;Team Europcar&#x9;27&#x9;151
188&#x9; Pierre Rolland&#x9; France&#x9;Team Europcar&#x9;24*&#x9;11
189&#x9;S&#xFFFD;bastien Turgot&#x9; France&#x9;Team Europcar&#x9;27&#x9;120
191&#x9;Vladimir Karpets&#x9; Russia&#x9;Team Katusha&#x9;30&#x9;28
192&#x9;Pavel Brutt&#x9; Russia&#x9;Team Katusha&#x9;29&#x9;DNF-9
193&#x9;Denis Galimzyanov&#x9; Russia&#x9;Team Katusha&#x9;24*&#x9;HD-12
194&#x9;Vladimir Gusev&#x9; Russia&#x9;Team Katusha&#x9;28&#x9;23
195&#x9;Mikhail Ignatiev&#x9; Russia&#x9;Team Katusha&#x9;26&#x9;147
196&#x9;Vladimir Isaichev&#x9; Russia&#x9;Team Katusha&#x9;25*&#x9;DNF-13
197&#x9;Alexandr Kolobnev&#x9; Russia&#x9;Team Katusha&#x9;30&#x9;DNS-10
198&#x9;Egor Silin&#x9; Russia&#x9;Team Katusha&#x9;23*&#x9;73
199&#x9;Yuri Trofimov&#x9; Russia&#x9;Team Katusha&#x9;27&#x9;30
201&#x9;Romain Feillu&#x9; France&#x9;Vacansoleil-DCM&#x9;27&#x9;DNS-12
202&#x9;Borut Boic&#x9; Slovenia&#x9;Vacansoleil-DCM&#x9;30&#x9;136
203&#x9;Thomas De Gendt&#x9; Belgium&#x9;Vacansoleil-DCM&#x9;24*&#x9;63
204&#x9;Johnny Hoogerland&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;28&#x9;74
205&#x9;Bj&#xFFFD;rn Leukemans&#x9; Belgium&#x9;Vacansoleil-DCM&#x9;34&#x9;HD-19
206&#x9;Marco Marcato&#x9; Italy&#x9;Vacansoleil-DCM&#x9;27&#x9;89
207&#x9;Wout Poels&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;23*&#x9;DNF-9
208&#x9;Rob Ruijgh&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;24*&#x9;21
209&#x9;Lieuwe Westra&#x9; Netherlands&#x9;Vacansoleil-DCM&#x9;28&#x9;128
211&#x9;J&#xFFFD;r&#xFFFD;me Coppel&#x9; France&#x9;Saur-Sojasun&#x9;24*&#x9;14
212&#x9;Arnaud Coyot&#x9; France&#x9;Saur-Sojasun&#x9;30&#x9;148
213&#x9;Anthony Delaplace&#x9; France&#x9;Saur-Sojasun&#x9;21*&#x9;135
214&#x9;Jimmy Engoulvent&#x9; France&#x9;Saur-Sojasun&#x9;31&#x9;160
215&#x9;J&#xFFFD;r&#xFFFD;mie Galland&#x9; France&#x9;Saur-Sojasun&#x9;28&#x9;138
216&#x9;Jonathan Hivert&#x9; France&#x9;Saur-Sojasun&#x9;26&#x9;97
217&#x9;Fabrice Jeandesboz&#x9; France&#x9;Saur-Sojasun&#x9;26&#x9;124
218&#x9;Laurent Mangel&#x9; France&#x9;Saur-Sojasun&#x9;30&#x9;122
219&#x9;Yannick Talabardon&#x9; France&#x9;Saur-Sojasun&#x9;29&#x9;47
'''

def init_riders():
	large_delete_all( Rider )

	tdf = tdf.strip()
	lines = tdf.split( '\n' )
	with transaction.atomic():
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
			
			safe_print( first_name, last_name, team, gender, date_of_birth, license )
			r = Rider( first_name=first_name.encode('iso-8859-1'), last_name=last_name.encode('iso-8859-1'), team=team.encode('iso-8859-1'), gender=gender, date_of_birth=date_of_birth, license=license )
			r.save()

