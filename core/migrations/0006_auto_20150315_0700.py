# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20150311_2042'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='ftp_host',
            field=models.CharField(default=b'', max_length=80, verbose_name='FTP Host', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='ftp_password',
            field=models.CharField(default=b'', max_length=64, verbose_name='FTP Password', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='ftp_path',
            field=models.CharField(default=b'', max_length=256, verbose_name='FTP Path', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='ftp_user',
            field=models.CharField(default=b'', max_length=80, verbose_name='FTP User', blank=True),
            preserve_default=True,
        ),
    ]
