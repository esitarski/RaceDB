# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

	dependencies = [
		('core', '0029_licenseholder_phone'),
	]

	operations = [
		migrations.AlterUniqueTogether(
			name='numbersetentry',
			unique_together=set([('number_set', 'bib')]),
		),
	]
