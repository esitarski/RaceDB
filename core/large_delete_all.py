from django.db import transaction

def large_delete_all( Object ):
	while Object.objects.count():
		with transaction.atomic():
			ids = Object.objects.values_list('pk', flat=True)[:999]
			Object.objects.filter(pk__in=ids).delete()
