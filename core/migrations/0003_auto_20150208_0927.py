# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import core.DurationField


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20150201_1649'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='est_kmh',
            field=models.FloatField(default=0.0, verbose_name='Est Kmh'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventmassstart',
            name='optional',
            field=models.BooleanField(default=False, help_text='Allows Participants to choose whether to enter.  Otherwise the Event is included for all participants.', verbose_name='Optional'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventtt',
            name='optional',
            field=models.BooleanField(default=False, help_text='Allows Participants to choose whether to enter.  Otherwise the Event is included for all participants.', verbose_name='Optional'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wavett',
            name='fastest_participants_start_gap',
            field=core.DurationField.DurationField(default=120, verbose_name='Fastest Participants Start Gap (FSG)'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wavett',
            name='gap_before_wave',
            field=core.DurationField.DurationField(default=300, verbose_name='Gap Before Wave (GBW)'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wavett',
            name='num_fastest_participants',
            field=models.PositiveSmallIntegerField(default=5, help_text=b'Participants to get the Fastest gap', verbose_name='Number of Fastest Participants (NFP)', choices=[(0, b'0'), (1, b'1'), (2, b'2'), (3, b'3'), (4, b'4'), (5, b'5'), (6, b'6'), (7, b'7'), (8, b'8'), (9, b'9'), (10, b'10'), (11, b'11'), (12, b'12'), (13, b'13'), (14, b'14'), (15, b'15')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='wavett',
            name='regular_start_gap',
            field=core.DurationField.DurationField(default=60, verbose_name='Regular Start Gap (RSG)'),
            preserve_default=True,
        ),
    ]
