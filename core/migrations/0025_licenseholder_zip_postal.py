# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20150902_1850'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseholder',
            name='zip_postal',
            field=models.CharField(default=b'', max_length=12, verbose_name='Zip/Postal', blank=True),
        ),
    ]
