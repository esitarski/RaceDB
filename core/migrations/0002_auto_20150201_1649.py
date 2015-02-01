# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import core.DurationField


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntryTT',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('est_speed', models.FloatField(default=0.0, verbose_name='Est. Speed')),
                ('hint_sequence', models.PositiveIntegerField(default=0, verbose_name='Hint Sequence')),
                ('start_sequence', models.PositiveIntegerField(default=0, verbose_name='Start Sequence', db_index=True)),
                ('start_time', core.DurationField.DurationField(null=True, verbose_name='Start Time', blank=True)),
                ('finish_time', core.DurationField.DurationField(null=True, verbose_name='Finish Time', blank=True)),
                ('adjustment_time', core.DurationField.DurationField(null=True, verbose_name='Adjustment Time', blank=True)),
                ('adjustment_note', models.CharField(default=b'', max_length=128, verbose_name='Adjustment Note')),
            ],
            options={
                'ordering': ['start_time'],
                'verbose_name': 'Time Trial Entry',
                'verbose_name_plural': 'Time Trial Entry',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventTT',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('date_time', models.DateTimeField(verbose_name='Date Time', db_index=True)),
                ('event_type', models.PositiveSmallIntegerField(default=0, verbose_name=b'Event Type', choices=[(0, 'Mass Start'), (1, 'Time Trial')])),
                ('optional', models.BooleanField(default=False, help_text='Otherwise this Event is included for all Participants', verbose_name='Optional')),
                ('option_id', models.PositiveIntegerField(default=0, verbose_name='Option Id')),
                ('competition', models.ForeignKey(to='core.Competition')),
            ],
            options={
                'verbose_name': 'Time Trial Event',
                'verbose_name_plural': 'Time Trial Events',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ParticipantOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('option_id', models.PositiveIntegerField(verbose_name=b'Option Id')),
                ('competition', models.ForeignKey(to='core.Competition')),
                ('participant', models.ForeignKey(to='core.Participant')),
            ],
            options={
                'verbose_name': 'Participant Option',
                'verbose_name_plural': 'Participant Options',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WaveTT',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('distance', models.FloatField(null=True, verbose_name='Distance', blank=True)),
                ('laps', models.PositiveSmallIntegerField(null=True, verbose_name='Laps', blank=True)),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence')),
                ('gap_before_wave', core.DurationField.DurationField(default=300, verbose_name='Gap Before Wave')),
                ('regular_start_gap', core.DurationField.DurationField(default=60, verbose_name='Regular Start Gap')),
                ('fastest_participants_start_gap', core.DurationField.DurationField(default=120, verbose_name='Fastest Participants Start Gap')),
                ('num_fastest_participants', models.PositiveSmallIntegerField(default=5, help_text=b'Number of participants to get Fastest participants gap', verbose_name='Number of Fastest Participants', choices=[(0, b'0'), (1, b'1'), (2, b'2'), (3, b'3'), (4, b'4'), (5, b'5'), (6, b'6'), (7, b'7'), (8, b'8'), (9, b'9'), (10, b'10'), (11, b'11'), (12, b'12'), (13, b'13'), (14, b'14'), (15, b'15')])),
                ('categories', models.ManyToManyField(to='core.Category', verbose_name='Categories')),
                ('event', models.ForeignKey(to='core.EventTT')),
            ],
            options={
                'ordering': ['sequence'],
                'verbose_name': 'TTWave',
                'verbose_name_plural': 'TTWaves',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='participantoption',
            unique_together=set([('competition', 'participant', 'option_id')]),
        ),
        migrations.AlterIndexTogether(
            name='participantoption',
            index_together=set([('competition', 'option_id'), ('competition', 'participant'), ('competition', 'participant', 'option_id')]),
        ),
        migrations.AddField(
            model_name='entrytt',
            name='event',
            field=models.ForeignKey(verbose_name='Event', to='core.EventTT'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entrytt',
            name='participant',
            field=models.ForeignKey(verbose_name='Participant', to='core.Participant'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='entrytt',
            unique_together=set([('event', 'participant')]),
        ),
        migrations.AlterIndexTogether(
            name='entrytt',
            index_together=set([('event', 'start_sequence')]),
        ),
        migrations.AddField(
            model_name='eventmassstart',
            name='option_id',
            field=models.PositiveIntegerField(default=0, verbose_name='Option Id'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventmassstart',
            name='optional',
            field=models.BooleanField(default=False, help_text='Otherwise this Event is included for all Participants', verbose_name='Optional'),
            preserve_default=True,
        ),
    ]
