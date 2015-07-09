# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_competition_ftp_upload_during_race'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='ga_tracking_id',
            field=models.CharField(default=b'', max_length=20, verbose_name='Google Analytics Tracking ID', blank=True),
            preserve_default=True,
        ),
    ]
