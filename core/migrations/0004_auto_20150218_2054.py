# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20150218_0914'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmassstart',
            name='select_by_default',
            field=models.BooleanField(default=False, help_text='If True, participants will be automatically added to the event, but can opt-out later.', verbose_name='Select by Default'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventtt',
            name='select_by_default',
            field=models.BooleanField(default=False, help_text='If True, participants will be automatically added to the event, but can opt-out later.', verbose_name='Select by Default'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventmassstart',
            name='optional',
            field=models.BooleanField(default=False, help_text='Allows Participants to choose to enter.  Otherwise the Event is included for all participants.', verbose_name='Optional'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventtt',
            name='optional',
            field=models.BooleanField(default=False, help_text='Allows Participants to choose to enter.  Otherwise the Event is included for all participants.', verbose_name='Optional'),
            preserve_default=True,
        ),
    ]
