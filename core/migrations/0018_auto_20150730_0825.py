# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20150726_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmassstart',
            name='road_race_finish_times',
            field=models.BooleanField(default=False, help_text='Ignore decimals, groups get same time', verbose_name='Road Race Finish Times'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventtt',
            name='road_race_finish_times',
            field=models.BooleanField(default=False, help_text='Ignore decimals, groups get same time', verbose_name='Road Race Finish Times'),
            preserve_default=True,
        ),
    ]
