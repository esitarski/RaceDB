# Generated by Django 5.1.1 on 2024-10-26 18:08

from django.db import migrations, models


# Ignore exceptions from RenameIndex which can occure if the old indexes don't exist.
from core.IgnoreException import IgnoreExceptionSubclass
RenameIndexIgnoreException = IgnoreExceptionSubclass( migrations.RenameIndex )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0034_alter_series_description_alter_series_name'),
    ]

    operations = [
        RenameIndexIgnoreException(
            model_name='entrytt',
            new_name='core_entryt_event_i_f9f4e7_idx',
            old_name='_7ead293751ac7bbc',
        ),
        RenameIndexIgnoreException(
            model_name='participantoption',
            new_name='core_partic_competi_36c115_idx',
            old_name='_52f168109ee938c5',
        ),
        RenameIndexIgnoreException(
            model_name='participantoption',
            new_name='core_partic_competi_c665bb_idx',
            old_name='_3cc9cee269af4411',
        ),
        RenameIndexIgnoreException(
            model_name='participantoption',
            new_name='core_partic_competi_21c187_idx',
            old_name='_45fc651eac7747a4',
        ),
    
        migrations.AddField(
            model_name='resultmassstart',
            name='result_note',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Result Note'),
        ),
        migrations.AddField(
            model_name='resulttt',
            name='result_note',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Result Note'),
        ),
    ]
