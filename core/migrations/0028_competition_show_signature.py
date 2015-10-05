# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20150918_1041'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='show_signature',
            field=models.BooleanField(default=True, verbose_name='Show Signature in Participant Edit Screen'),
        ),
    ]
