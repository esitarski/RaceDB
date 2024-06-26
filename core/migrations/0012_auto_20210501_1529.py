# Generated by Django 3.2 on 2021-05-01 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20200521_1644'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systeminfo',
            name='date_Md',
            field=models.CharField(choices=[('M d', 'MonthAbbr, day'), ('d M', 'day, MonthAbbr')], default='M d', max_length=24, verbose_name='Month Day Format'),
        ),
        migrations.AlterField(
            model_name='systeminfo',
            name='date_short',
            field=models.CharField(choices=[('Y-m-d', 'yyyy-mm-dd (ISO)'), ('d-m-Y', 'dd-mm-yyyy (UK)'), ('m-d-Y', 'mm-dd-yyyy USA)')], default='Y-m-d', max_length=24, verbose_name='Date Short Format'),
        ),
        migrations.AlterField(
            model_name='systeminfo',
            name='time_hhmmss',
            field=models.CharField(choices=[('H:i:s', 'HH:mm:ss (ISO: 24 hour)'), ('h:i:s P', 'hh:mm:ss AM/PM (NA: 12 hour AM/PM)')], default='H:i:s', max_length=24, verbose_name='Time Short Format'),
        ),
    ]
