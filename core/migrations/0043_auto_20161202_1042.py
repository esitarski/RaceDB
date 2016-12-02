# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-12-02 15:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_auto_20161124_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseholder',
            name='nation_code',
            field=models.CharField(blank=True, default=b'', max_length=3, verbose_name='Nation Code'),
        ),
        migrations.AddField(
            model_name='licenseholder',
            name='uci_id',
            field=models.CharField(blank=True, db_index=True, default=b'', max_length=11, verbose_name='UCI ID'),
        ),
    ]
