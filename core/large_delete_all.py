from django.db import transaction, connection
from django.db.models import Q

def large_delete_all( Object, query=None ):
	if query is None:
		query = Q()
	if connection.vendor == 'sqlite':
		while Object.objects.filter(query).exists():
			with transaction.atomic():
				ids = Object.objects.filter(query).values_list('pk')[:999]
				Object.objects.filter(pk__in=ids).delete()
	else:
		Object.objects.filter(query).delete()
