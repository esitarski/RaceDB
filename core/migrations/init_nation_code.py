# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, transaction

def init_nation_code(apps, schema_editor):
	LicenseHolder = apps.get_model("core", "LicenseHolder")
	
	success = True
	while success:
		with transaction.atomic():
			success = False
			for lh in LicenseHolder.objects.filter(nation_code__exact='').exclude(uci_code__exact='')[:999]:
				lh.nation_code = lh.uci_code[:3]
				lh.save()
				success = True

class Migration(migrations.Migration):

	dependencies = [
		('core', '0043_auto_20161202_1042'),
	]

	operations = [
		migrations.RunPython(init_nation_code),
	]
