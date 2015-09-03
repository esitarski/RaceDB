# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20150820_0731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='organizer_email',
            field=models.EmailField(max_length=254, verbose_name='Organizer Email', blank=True),
        ),
        migrations.AlterField(
            model_name='licenseholder',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
