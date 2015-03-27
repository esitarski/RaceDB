# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_systeminfo_exclude_empty_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systeminfo',
            name='exclude_empty_categories',
            field=models.BooleanField(default=True, help_text='Exclude empty categories from CrossMgr Excel', verbose_name='Exclude Empty Categories from CrossMgr'),
            preserve_default=True,
        ),
    ]
