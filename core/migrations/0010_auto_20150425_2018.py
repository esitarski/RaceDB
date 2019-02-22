# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_systeminfo_reg_allow_add_multiple_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seasonspassholder',
            name='license_holder',
            field=models.ForeignKey(verbose_name='LicenseHolder', to='core.LicenseHolder', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='seasonspassholder',
            unique_together=set([('seasons_pass', 'license_holder')]),
        ),
    ]
