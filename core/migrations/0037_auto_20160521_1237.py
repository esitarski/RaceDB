# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20160428_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='systeminfo',
            name='print_tag_option',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Print Tag Option', choices=[(0, 'No Bib Tag Print (Hide Print Bib Tag Button)'), (1, 'Print Bib Tag on Server (use command)'), (2, 'Print Bib Tag on Client (print from browser)')]),
        ),
        migrations.AddField(
            model_name='systeminfo',
            name='server_print_tag_cmd',
            field=models.CharField(default='lpr "$1"', max_length=160, verbose_name='Cmd used to print Bib Tag (parameter is PDF file})'),
        ),
    ]
