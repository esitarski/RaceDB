# Generated by Django 4.2 on 2023-05-24 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_primett_primemassstart'),
    ]

    operations = [
        migrations.AlterField(
            model_name='primemassstart',
            name='effort',
            field=models.SmallIntegerField(choices=[(0, 'Pack'), (1, 'Break'), (2, 'Chase'), (-1, 'Custom')], default=0, verbose_name='Effort'),
        ),
        migrations.AlterField(
            model_name='primett',
            name='effort',
            field=models.SmallIntegerField(choices=[(0, 'Pack'), (1, 'Break'), (2, 'Chase'), (-1, 'Custom')], default=0, verbose_name='Effort'),
        ),
    ]
