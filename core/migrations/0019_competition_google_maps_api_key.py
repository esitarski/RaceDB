# Generated by Django 3.2.6 on 2021-10-16 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_wavett_sequence_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='google_maps_api_key',
            field=models.CharField(blank=True, default='AIzaSyD2sl2JTvnyMcsgWc3tTceWCYo3ZoyWdAI', max_length=64, verbose_name='Google Maps API Key'),
        ),
    ]
