# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20150514_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='ftp_upload_during_race',
            field=models.BooleanField(default=False, verbose_name='Live FTP Update During Race'),
            preserve_default=True,
        ),
    ]
