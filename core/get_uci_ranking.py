import re
import os
import time
import string
import requests
import datetime
from .models import UCIRank

import unicodedata

def remove_diacritics(s):
	return ''.join(
		c for c in unicodedata.normalize('NFD', s)
		if unicodedata.category(c) != 'Mn'
	)

# Key parameters (update if the UCI site changes):
SeasonId = 453        # 2026

# rankingId, CategoryId, RaceTypeId — update from DevTools (https://www.uci.org/discipline/mountain-bike/4LArSj7CKcytMrGEDtKwkb?tab=rankings)
# Devtools: Network: Payload - trigger the query from the web page, select the last Name: ObjectRankings/, then select Payload.
CATEGORY_CONFIG = {
	# XCO
    "XME": {"label": "XCO Men Elite",    "rankingId": "148", "categoryId": "22", "RaceTypeId": 92, "disciplineId":7 },
    "XWE": {"label": "XCO Women Elite",  "rankingId": "155", "categoryId": "23", "RaceTypeId": 92, "disciplineId":7 },
    "XMJ": {"label": "XCO Men Junior",   "rankingId": "153", "categoryId": "24", "RaceTypeId": 92, "disciplineId":7 },
    "XWJ": {"label": "XCO Women Junior", "rankingId": "160", "categoryId": "25", "RaceTypeId": 92, "disciplineId":7 },

	# DH
    "DME": {"label": "DH Men Elite",     "rankingId": "149", "categoryId": "22", "RaceTypeId": 19, "disciplineId":7 },
    "DWE": {"label": "DH Women Elite",   "rankingId": "156", "categoryId": "23", "RaceTypeId": 19, "disciplineId":7 },

	# Road
    "RME": {"label": "Road Men Elite",    "rankingId": "1", "categoryId": "22", "RaceTypeId": 0, "disciplineId":10 },
    "RMU": {"label": "Road Men U23",      "rankingId": "342", "categoryId": "26", "RaceTypeId": 1, "disciplineId":10 },
    "RWE": {"label": "Road Women Elite",   "rankingId": "32", "categoryId": "23", "RaceTypeId": 0, "disciplineId":10 },

	# Cyclocross
	# This uses a different SeasonId (FIXLATER).
    "CME": {"label": "Cyclocross Men Elite",    "rankingId": "163", "categoryId": "22", "RaceTypeId": 0, "disciplineId":3 },
    "CMJ": {"label": "Cyclocross Men Junior",   "rankingId": "168", "categoryId": "24", "RaceTypeId": 9, "disciplineId":3 },
    "CWE": {"label": "Cyclocross Women Elite",  "rankingId": "168", "categoryId": "23", "RaceTypeId": 0, "disciplineId":3 },
    "CWJ": {"label": "Cyclocross Women Junior", "rankingId": "312", "categoryId": "25", "RaceTypeId": 0, "disciplineId":3 },
}

API_URL = "https://dataride.uci.ch/iframe/ObjectRankings/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UCI-rank-lookup/1.0)",
    "Accept":     "application/json, text/plain, */*",
    "Referer":    "https://www.uci.org/",
    "Origin":     "https://www.uci.org",
}

def build_payload(ranking_id, category_id, race_type_id, discipline_id, name=""):
    return {
        "rankingId":                     ranking_id,
        "disciplineId":                  discipline_id,
        "rankingTypeId":                 "1",
        "take":                          "5000",
        "skip":                          "0",
        "page":                          "1",
        "pageSize":                      "5000",
        "filter[filters][0][field]":     "RaceTypeId",
        "filter[filters][0][value]":     race_type_id,
        "filter[filters][1][field]":     "CategoryId",
        "filter[filters][1][value]":     category_id,
        "filter[filters][2][field]":     "SeasonId",
        "filter[filters][2][value]":     SeasonId,
        "filter[filters][3][field]":     "MomentId",
        "filter[filters][3][value]":     "0",
        "filter[filters][4][field]":     "CountryId",
        "filter[filters][4][value]":     "0",
        "filter[filters][5][field]":     "IndividualName",
        "filter[filters][5][value]":     name,
        "filter[filters][6][field]":     "TeamName",
        "filter[filters][6][value]":     "",
    }


def lookup(session, ranking_id, category_id, race_type_id, discipline_id, name=""):
	payload = build_payload(ranking_id, category_id, race_type_id, discipline_id, name)
	resp = session.post(API_URL, data=payload, headers=HEADERS, timeout=15)
	resp.raise_for_status()
	data = resp.json()

	items = (
		data.get("Data")
		or data.get("data")
		or data.get("items")
		or (data if isinstance(data, list) else [])
	)
	return items

def get_uci_rank_records( discipline_code ):
	
	def fix_date( v ):
		prefix = '/Date('
		suffix = ')/'
		if v.startswith(prefix) and v.endswith(suffix):
			ms = int(v[len(prefix):-len(suffix)])
			if ms == -62135596800000:	# Check for .NET reserved None value.
				v = None
			else:
				try:
					v = datetime.datetime.fromtimestamp(ms / 1000).date()
				except Exception as e:
					print( f'fix_date: Error: {v}: {e}' )
		return v
	
	def get_last_first( n ):
		is_last = True
		last, first = [], []
		for n in n.split( ' ' ):
			# Remove all accents (required for dataride upload).
			n = remove_diacritics( n )
			# Check for at least one alpha-numeric character.
			if not bool(re.search(r'[a-zA-Z0-9]', n)):
				continue
			if is_last and n == n.upper():
				last.append( n )
			else:
				is_last = False
				first.append( n )
		return ' '.join( last ), ' '.join( first )
	
	all_results = []

	session = requests.Session()

	ignore_fields = (
		'ObjectId', 'ObjectTypeId',
		'PrecedingRank',
		'FullName', 'DisciplineId', 'RankingInformation', 'MandatoryDate',
		'ResultTeamTypeId', 'RankingId', 'GroupId', 'MomentId',
		'BaseRankingTypeId', 'Rankinginformation', 
		'MandatoryDate', 'CompetitionName',
		'CategoryName', 'RaceTypeName',
		'EventTypeName', 'LegalSelectionCode', 'IndividualEventRankings', 'TotalIndividualEventRankings',
		'ClassId', 'ClassCode', 'RankDifference', 'DisplayTeam', 'Position',
	)

	# Query all categories of this discipline.
	cats = [c for c in CATEGORY_CONFIG.keys() if c.startswith(discipline_code)]
	for category in cats:
		gender_code = category[1]
		cat_cfg = CATEGORY_CONFIG[category]
		try:
			results = lookup(session, cat_cfg["rankingId"], cat_cfg["categoryId"], cat_cfg["RaceTypeId"], cat_cfg["disciplineId"])
		except requests.HTTPError as e:
			print(f"{name:<22} ERROR: {e}")
			#results.append({"searched": name, "rank": "ERROR", "uci_id": "",
			#				  "name": str(e), "nationality": "", "team": "", "points": ""})
			continue
		
		# Fix the uciid and set the full category.
		for r in results:
			for k in ignore_fields:
				try:
					del r[k]
				except KeyError:
					pass
			
			r['Rank'] = int(r['Rank'])
			
			if r['DisplayName'].startswith( '* ' ):
				r['DisplayName'] = r['DisplayName'][2:]
			
			age = int(r['Ages'])
			if age < 19:
				category = f'{discipline_code}{gender_code}J'
			elif age < 23:
				category = f'{discipline_code}{gender_code}U'
			else:
				category = f'{discipline_code}{gender_code}E'
				
			r['Category'] = category
			r['LastName'], r['FirstName'] = get_last_first( r['IndividualFullName'] )			
			
			for k in r.keys():
				if k.endswith('Date'):
					r[k] = fix_date( r[k] )
		
		all_results.extend( results )
		time.sleep(0.5)
			
	session.close()

	return all_results

def get_discipline_code( competition ):
	category_format = competition.category_format
	for category in category_format.category_set.all():
		# X - MTB Cross Country
		# D - MTB Downhill
		# R - Road
		# C - Cyclocross
		if category.code[0] in 'XDRC':
			return category.code[0]
	return 'X'

def get_uci_rank( competition ):		
	records = get_uci_rank_records( get_discipline_code(competition) )
	
	to_add = []
	uci_id_seen = set()
	for uci_record in records:
		fields = { field:convert(uci_record[key]) for field, key, convert in UCIRank.FieldMap }
		ur = UCIRank( competition=competition, **fields )
		# Ensure that all the uci_ids are unique.
		if ur.uci_id and ur.uci_id not in uci_id_seen:
			to_add.append( ur )
			uci_id_seen.add( ur.uci_id )
	
	UCIRank.objects.filter( competition=competition ).delete()
	UCIRank.objects.bulk_create( to_add )
