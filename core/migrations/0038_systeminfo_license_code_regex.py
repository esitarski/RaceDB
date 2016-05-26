# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_auto_20160521_1237'),
    ]

    operations = [
        migrations.AddField(
            model_name='systeminfo',
            name='license_code_regex',
            field=models.CharField(default=b'', help_text='Must include a license_code field.  For example, "[^;]*;(?P&lt;license_code&gt;[^?]*).*"', max_length=160, verbose_name='License Code Regex', blank=True),
        ),
    ]
