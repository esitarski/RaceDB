# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_auto_20160119_2050'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalEntity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('contact', models.CharField(default=b'', max_length=64, verbose_name='Contact', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='Email', blank=True)),
                ('phone', models.CharField(default=b'', max_length=22, verbose_name='Phone', blank=True)),
                ('website', models.CharField(default=b'', max_length=255, verbose_name='Website', blank=True)),
                ('waiver_expiry_date', models.DateField(default=datetime.date(1970, 1, 1), verbose_name='Waiver Expiry Date', db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'LegalEntity',
                'verbose_name_plural': 'LegalEntities',
            },
        ),
        migrations.CreateModel(
            name='Waiver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_signed', models.DateField(default=None, null=True, verbose_name='Waiver Signed on', db_index=True)),
                ('legal_entity', models.ForeignKey(to='core.LegalEntity', on_delete=models.CASCADE)),
                ('license_holder', models.ForeignKey(to='core.LicenseHolder', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Waiver',
                'verbose_name_plural': 'Waivers',
            },
        ),
        migrations.AddField(
            model_name='competition',
            name='legal_entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Legal Entity', blank=True, to='core.LegalEntity', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='waiver',
            unique_together=set([('license_holder', 'legal_entity')]),
        ),
    ]
