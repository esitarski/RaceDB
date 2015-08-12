# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_wavett_sequence_option'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wavett',
            name='sequence_option',
            field=models.PositiveSmallIntegerField(default=0, help_text=b'Criteria used to order participants in the wave', verbose_name='Sequence Option', choices=[('Increasing', ((0, 'Est. Speed - Increasing'), (1, 'Age - Increasing'), (2, 'Bib - Increasing'))), ('Decreasing', ((3, 'Age - Decreasing'), (4, 'Bib - Decreasing')))]),
            preserve_default=True,
        ),
    ]
