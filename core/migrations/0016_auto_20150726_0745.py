# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20150726_0738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systeminfo',
            name='tag_template',
            field=models.CharField(help_text='Template for generating EPC RFID tags from Database ID.', max_length=24, verbose_name='Tag Template'),
            preserve_default=True,
        ),
    ]
