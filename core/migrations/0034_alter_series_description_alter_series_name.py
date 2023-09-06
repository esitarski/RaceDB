# Generated by Django 4.2.3 on 2023-07-31 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_alter_competition_gpx_course_default_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='series',
            name='description',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='series',
            name='name',
            field=models.CharField(default='MySeries', max_length=128, verbose_name='Name'),
        ),
    ]