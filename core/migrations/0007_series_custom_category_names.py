# Generated by Django 2.2.1 on 2019-08-30 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20190722_0859'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='custom_category_names',
            field=models.TextField(blank=True, default='', verbose_name='Custom Categories'),
        ),
    ]
