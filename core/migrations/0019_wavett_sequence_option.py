# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20150730_0825'),
    ]

    operations = [
        migrations.AddField(
            model_name='wavett',
            name='sequence_option',
            field=models.PositiveSmallIntegerField(default=0, help_text=b'Sequence logic used to order participants in the wave', verbose_name='Sequence Option'),
            preserve_default=True,
        ),
    ]
