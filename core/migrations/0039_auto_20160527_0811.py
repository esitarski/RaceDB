# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_systeminfo_license_code_regex'),
    ]

    operations = [
        migrations.AddField(
            model_name='numberset',
            name='description',
            field=models.CharField(default=b'', max_length=80, verbose_name='Description', blank=True),
        ),
        migrations.AddField(
            model_name='numberset',
            name='sponsor',
            field=models.CharField(default=b'', max_length=80, verbose_name='Sponsor', blank=True),
        ),
    ]
