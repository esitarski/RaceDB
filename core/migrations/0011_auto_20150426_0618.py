# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20150425_2018'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmassstart',
            name='note',
            field=models.TextField(null=True, verbose_name='Note', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventtt',
            name='note',
            field=models.TextField(null=True, verbose_name='Note', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='licenseholder',
            name='note',
            field=models.TextField(null=True, verbose_name='LicneseHolder Note', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='numbersetentry',
            name='date_lost',
            field=models.DateField(default=None, null=True, verbose_name='Date Lost', db_index=True),
            preserve_default=True,
        ),
    ]
