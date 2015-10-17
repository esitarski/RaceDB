# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_competition_show_signature'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseholder',
            name='phone',
            field=models.CharField(default=b'', max_length=26, verbose_name='Phone', blank=True),
        ),
    ]
