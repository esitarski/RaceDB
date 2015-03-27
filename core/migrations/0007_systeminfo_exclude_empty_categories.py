# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20150315_0700'),
    ]

    operations = [
        migrations.AddField(
            model_name='systeminfo',
            name='exclude_empty_categories',
            field=models.BooleanField(default=True, help_text='Exclude empty categories from CrossMgr output', verbose_name='Exclude Empty Categories'),
            preserve_default=True,
        ),
    ]
