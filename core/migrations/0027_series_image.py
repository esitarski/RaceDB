# Generated by Django 4.2 on 2023-05-23 18:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_competition_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='series',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.image', verbose_name='Image'),
        ),
    ]
