# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20150326_2148'),
    ]

    operations = [
        migrations.AddField(
            model_name='systeminfo',
            name='reg_allow_add_multiple_categories',
            field=models.BooleanField(default=True, help_text='If True, reg staff can add participants to Multiple Categories (eg. race up a catgegory).  If False, only "super" can do so.', verbose_name='Allow "reg" to Add Participants to Multiple Categories'),
            preserve_default=True,
        ),
    ]
