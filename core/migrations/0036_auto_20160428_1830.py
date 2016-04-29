# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_competition_recurring'),
    ]

    operations = [
        migrations.AddField(
            model_name='wave',
            name='max_participants',
            field=models.PositiveIntegerField(null=True, verbose_name='Max Participants', blank=True),
        ),
        migrations.AddField(
            model_name='wavett',
            name='max_participants',
            field=models.PositiveIntegerField(null=True, verbose_name='Max Participants', blank=True),
        ),
    ]
