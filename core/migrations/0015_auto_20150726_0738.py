# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_competition_ga_tracking_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='systeminfo',
            name='tag_from_license',
            field=models.BooleanField(default=False, help_text='Generate RFID tag from license (not database id)', verbose_name='RFID Tag from License'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='systeminfo',
            name='tag_from_license_id',
            field=models.PositiveSmallIntegerField(default=0, help_text='Identifier is added to the tag for additional recognition.', verbose_name='Identifier', choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'), (13, '13'), (14, '14'), (15, '15'), (16, '16'), (17, '17'), (18, '18'), (19, '19'), (20, '20'), (21, '21'), (22, '22'), (23, '23'), (24, '24'), (25, '25'), (26, '26'), (27, '27'), (28, '28'), (29, '29'), (30, '30'), (31, '31')]),
            preserve_default=True,
        ),
    ]
