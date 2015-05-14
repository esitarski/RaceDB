# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20150426_0618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licenseholder',
            name='note',
            field=models.TextField(null=True, verbose_name='LicenseHolder Note', blank=True),
            preserve_default=True,
        ),
    ]
