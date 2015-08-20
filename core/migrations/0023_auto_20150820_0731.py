# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20150812_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseholder',
            name='emergency_contact_name',
            field=models.CharField(default=b'', max_length=64, verbose_name='Emergency Contact', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='licenseholder',
            name='emergency_contact_phone',
            field=models.CharField(default=b'', max_length=26, verbose_name='Emergency Contact Phone', blank=True),
            preserve_default=True,
        ),
    ]
