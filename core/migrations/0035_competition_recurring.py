# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_participant_seed_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='recurring',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Recurring', choices=[(0, b'-'), (7, 'Every Week'), (14, 'Every 2 Weeks'), (21, 'Every 3 Weeks'), (28, 'Every 4 Weeks')]),
        ),
    ]
