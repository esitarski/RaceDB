# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20150208_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventtt',
            name='create_seeded_startlist',
            field=models.BooleanField(default=True, help_text='If True, seeded start times will be generated in the startlist for CrossMgr.  If False, no seeded times will be generated, and the TT time will start on the first bib entry.', verbose_name='Create Seeded Startlist'),
            preserve_default=True,
        ),
    ]
