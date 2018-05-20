from django.db import transaction
from models import *
from large_delete_all import large_delete_all

disciplines = [
	'Road',
	'Track',
	'Cyclocross',
	'MTB',
	'BMX',
	'Para',
]

race_classes = [
	'Club',
	'Citizen',
	'Regional',
	'Reg. Champ.',
	'National',
	'UCI 1.HC',
	'UCI 2.HC',
	'UCI 1.1',
	'UCI 2.1',
	'UCI 1.2',
	'UCI 2.2',
	'UCI Ncup 1.2',
	'UCI Ncup 2.2',
	'UCI Wcup',
	'UCI 1.Ncup',
	'UCI 2.Ncup',
]

number_sets = [
	'Reference Number Set',
]

def init_static():
	for cls, values in [
			(Discipline, disciplines),
			(RaceClass, race_classes),
			(NumberSet, number_sets),
		]:
		large_delete_all( cls )
		with transaction.atomic():
			for i, name in enumerate(values):
				safe_print( i, name )
				cls( name = name, sequence = i ).save()
				
