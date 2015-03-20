from django.db import transaction
from django.db.models import Q

def large_delete_all( Object, query=None ):
	if query is None:
		query = Q()
	while Object.objects.filter(query).exists():
		with transaction.atomic():
			ids = Object.objects.filter(query).values_list('pk', flat=True)[:999]
			Object.objects.filter(pk__in=ids).delete()
