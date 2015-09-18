# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_licenseholder_zip_postal'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Label used for reporting.', max_length=32, verbose_name='Report Label')),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence')),
            ],
            options={
                'ordering': ['sequence'],
            },
        ),
        migrations.AddField(
            model_name='competition',
            name='report_labels',
            field=models.ManyToManyField(to='core.ReportLabel'),
        ),
    ]
