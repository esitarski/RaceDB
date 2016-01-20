# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_eventmassstart_win_and_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmassstart',
            name='dnsNoData',
            field=models.BooleanField(default=True, verbose_name='Show Participants with no race data as DNS'),
        ),
        migrations.AddField(
            model_name='eventtt',
            name='dnsNoData',
            field=models.BooleanField(default=True, verbose_name='Show Participants with no race data as DNS'),
        ),
    ]
