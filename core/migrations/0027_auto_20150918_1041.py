# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20150918_0827'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reportlabel',
            options={'ordering': ['sequence'], 'verbose_name': 'Report Label', 'verbose_name_plural': 'Report Labels'},
        ),
        migrations.AlterField(
            model_name='competition',
            name='report_labels',
            field=models.ManyToManyField(to='core.ReportLabel', verbose_name='Report Labels', blank=True),
        ),
    ]
