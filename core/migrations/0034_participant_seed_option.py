# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_auto_20160129_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='seed_option',
            field=models.SmallIntegerField(default=1, verbose_name='Seed Option', choices=[(1, 'None'), (0, 'Seed Early'), (2, 'Seed Late')]),
        ),
    ]
