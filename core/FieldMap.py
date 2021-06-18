import unicodedata

def remove_diacritic(input):
	'''
	Accept a unicode string, and return a normal string
	without any diacritical marks.
	'''
	return unicodedata.normalize('NFKD', u'{}'.format(input)).encode('ASCII', 'ignore').decode()

def normalize( s ):
	return remove_diacritic( s.replace('.','').replace('_',' ').strip().lower() )
 
class FieldMap( object ):
	def __init__( self ):
		self.reset()
		
	def reset( self ):
		self.name_to_col = {}
		self.alias_to_name = {}
		self.unmapped = set()
		self.aliases = {}
		self.description = {}
		 
	def set_aliases( self, name, aliases, description='' ):
		self.aliases[name] = tuple(aliases)
		for a in self.aliases[name]:
			self.alias_to_name[normalize(a)] = name
		self.description[name] = description

	def __delitem__( self, name ):
		for a in self.aliases[name]:
			del self.alias_to_name[normalize(a)]
		del self.aliases[name]
		del self.description[name]
		
	def get_aliases( self, name ):
		return self.aliases.get(name, tuple())
		
	def get_description( self, name ):
		return self.description.get(name, '')
			
	def set_headers( self, header ):
		self.name_to_col = {}
		self.unmapped = set()
		for i, h in enumerate(header):
			try:
				h = normalize( h )
			except Exception as e:
				continue
			
			try:
				name = self.alias_to_name[h]
			except KeyError:
				continue
			if name not in self.name_to_col:
				self.name_to_col[name] = i
			else:
				self.unmapped.add( h )
	
	def get_value( self, name, fields, default=None ):
		try:
			return fields[self.name_to_col[name]]
		except (KeyError, IndexError):
			return default
		
	def finder( self, fields ):
		return lambda name, default=None: self.get_value(name, fields, default)
			
	def __contains__( self, name ):
		return name in self.name_to_col
		
	def get_name_from_alias( self, alias ):
		try:
			alias = normalize( alias )
		except Exception as e:
			return None
		return None if alias in self.unmapped else self.alias_to_name.get(alias, None)

standard_field_aliases = (
	('last_name',
		('LastName','Last Name','LName','Rider Last Name',),
		"Participant's last name",
	),
	('first_name',
		('FirstName','First Name','FName','Rider First Name',),
		"Participant's first name",
	),
	('date_of_birth',
		('Date of Birth','DateOfBirth','Birthdate','DOB','Birth','Birthday',),
		"Date of birth",
	),
	('gender',
		('Gender', 'Rider Gender', 'Sex', 'Race Gender',),
		"Gender",
	),
	('team',
		('Team','Team Name','TeamName','Rider Team','RiderTeam','Trade Team','Rider Club/Team',),
		"Team",
	),
	('team_code',
		('Team Code','TeamCode',),
		"Team Code",
	),
	('club',
		('Club','Club Name','ClubName','Rider Club',),
		"Club",
	),
	('license_code',
		(
			'Lic', 'Lic #',
			'Lic Num', 'LicNum', 'Lic Number',
			'Lic Nums','LicNums','Lic Numbers',
			
			'License','License #', 
			'License Number','LicenseNumber',
			'License Numbers','LicenseNumbers',
			'License Num', 'LicenseNum',
			'License Nums','LicenseNums',
			'License Code','LicenseCode','LicenseCodes',
			
			'Rider License #',
		),
		"License code (not UCI code)",
	),
	('uci_code',
		('UCI Code','UCICode','UCI',),
		"UCI code of the form NNNYYYYMMDD",
	),
	('uci_id',
		('UCIID','UCI ID',),
		"UCI ID of the form XXX XXX XXX XX",
	),
	('bib',
		('Bib','BibNum','Bib Num','Bib Number','BibNumber','Bib #','Bib#','Rider Bib #','Rider Num'),
		"Bib number",
	),
	('paid',
		('Paid','Fee Paid',),
		"Paid",
	),
	('license_checked',
		('License Checked','License Check','Lic Checked','Lic Check','LicCheck',),
		"Licensed has been checked",
	),
	('license_check_required',
		('License Check Required',),
		"License Check Required",
	),
	('license_check_note',
		('License Check Note',),
		"License check note",
	),
	('email',
		('Email','Rider Email',),
		"Email",
	),
	('phone',
		('Phone','Phone Number','Phone Num','Phone #','Phone No','Telephone','Telephone Number','Telephone Num','Telephone #','Telephone No','Tel #','Tel No','Tel',),
		"Phone",
	),
	('city',
		('City',),
		"City",
	),
	('state_prov',
		('State','Prov','Province','Stateprov','State Prov',),
		"State or Province",
	),
	('nation_code',
		('Nation Code','NationCode','NatCode','Racing Nationality',),
		"Nation Code (3 letters)",
	),
	('nationality',
		('Nationality'),
		"Competitive nationality",
	),
	('tag',
		('Tag','Chip','Chip ID','Chip Tag','RFID',),
		"Chip tag",
	),
	('note',
		('Note',),
		"Note",
	),
	('zip_postal',
		('ZipPostal','Zip','Postal','Zip Code','Postal Code','ZipCode','PostalCode',),
		"Postal or Zip code",
	),
	('category_code',
		('Category','Category Code','Category_Code',),
		"Category",
	),
	('est_kmh',
		('Est kmh','Est. kmh','kmh',),
		"Estimated kmh (used for Time Trial Seeding)",
	),
	('est_mph',
		('Est mph','Est. mph','mph',),
		"Estimated mph (used for Time Trial Seeding)",
	),
	('seed_option',
		('Seed Option','SeedOption',),
		"Time Trial Seeding Option (value is 'early','late', 'last' or blank)",
	),
	('emergency_contact_name',
		('Emergency Contact','Emergency Contact Name','Emergency Name',),
		"Emergency Contact Name",
	),
	('emergency_contact_phone',
		('Emergency Phone','Emergency Contact Phone',),
		"Emergency Contact Phone",
	),
	('emergency_medical',
		('Emergency Medical','Medic Alert','MedicAlert','Medical Alert'),
		"Emergency Medical Alert",
	),
	('race_entered',
		('Race Entered','RaceEntered',),
		"Race Entered",
	),
	('role',
		('Role',),
		"Role",
	),
	('preregistered',
		('Preregistered', 'Prereg',),
		"Preregistered",
	),
	('waiver',
		('Waiver',),
		"Waiver",
	),
	('age',
		('Age','Competition Age'),
		"age",
	),
)

def standard_field_map( exclude = [] ):
	fm = FieldMap()
	for a in standard_field_aliases:
		fm.set_aliases( *a )
		if a[0] == 'license_code':
			for i in range(1,9):
				i_str = '{}'.format(i)
				lci = (
					a[0] + i_str,
					tuple( v + i_str for v in a[1] ),
					a[2] + i_str,
				)
				fm.set_aliases( *lci )
	for e in exclude:
		del fm[e]
	return fm
	
if __name__ == '__main__':
	sfm = standard_field_map()
	headers = ('BibNum', 'Role', 'license', 'UCI Code', 'note', 'tag', 'Emergency Phone')
	sfm.set_headers( headers )
	del sfm['note']
	
	row = (133, 'Competitor', 'ABC123', 'CAN19900925', 'Awesome', '123456', '415-789-5432')
	v = sfm.finder( row )
	print ( v('bib'), v('role'), v('license'), v('uci_code'), v('note'), v('tag'), v('emergency_contact_phone') )
	assert v('bib', None) == 133
	print ( sfm.get_aliases( 'license_code' ) )
