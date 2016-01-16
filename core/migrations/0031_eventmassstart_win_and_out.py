# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20151104_0621'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmassstart',
            name='win_and_out',
            field=models.BooleanField(default=False, verbose_name='Win and Out'),
        ),
    ]
