# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_auto_20160527_0811'),
    ]

    operations = [
        migrations.AddField(
            model_name='licenseholder',
            name='eligible',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Eligible to Compete'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='role',
            field=models.PositiveSmallIntegerField(default=110, verbose_name='Role', choices=[('Team', ((110, 'Competitor'), (120, 'Manager'), (130, 'Coach'), (140, 'Doctor'), (150, 'Paramedical Asst.'), (160, 'Mechanic'), (170, 'Driver'), (199, 'Staff'))), ('Official', ((210, 'Commissaire'), (220, 'Timer'), (230, 'Announcer'), (240, 'Radio Operator'), (250, 'Para Classifier'), (299, 'Official Staff'))), ('Organizer', ((310, 'Administrator'), (320, 'Organizer Mechanic'), (330, 'Organizer Driver'), (399, 'Organizer Staff'))), ('Press', ((410, 'Photographer'), (420, 'Reporter')))]),
        ),
    ]
