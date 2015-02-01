# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import core.DurationField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(default=b'', max_length=16, verbose_name='Code')),
                ('gender', models.PositiveSmallIntegerField(default=0, verbose_name='Gender', choices=[(0, 'Men'), (1, 'Women'), (2, 'Open')])),
                ('description', models.CharField(default=b'', max_length=80, verbose_name='Description', blank=True)),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence')),
            ],
            options={
                'ordering': ['sequence', '-gender', 'code'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryFormat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=32, verbose_name='Name')),
                ('description', models.CharField(default=b'', max_length=80, verbose_name='Description', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'CategoryFormat',
                'verbose_name_plural': 'CategoryFormats',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryHint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('effective_date', models.DateField(verbose_name='Effective Date', db_index=True)),
                ('category', models.ForeignKey(to='core.Category')),
            ],
            options={
                'verbose_name': 'CategoryHint',
                'verbose_name_plural': 'CategoryHints',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryNumbers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range_str', models.TextField(default=b'1-99,120-129,-50-60,181,-87', verbose_name='Range')),
                ('categories', models.ManyToManyField(to='core.Category')),
            ],
            options={
                'verbose_name': 'CategoryNumbers',
                'verbose_name_plural': 'CategoriesNumbers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('description', models.CharField(default=b'', max_length=80, verbose_name='Description', blank=True)),
                ('city', models.CharField(default=b'', max_length=64, verbose_name='City', blank=True)),
                ('stateProv', models.CharField(default=b'', max_length=64, verbose_name='StateProv', blank=True)),
                ('country', models.CharField(default=b'', max_length=64, verbose_name='Country', blank=True)),
                ('organizer', models.CharField(max_length=64, verbose_name='Organizer')),
                ('organizer_contact', models.CharField(default=b'', max_length=64, verbose_name='Organizer Contact', blank=True)),
                ('organizer_email', models.EmailField(max_length=75, verbose_name='Organizer Email', blank=True)),
                ('organizer_phone', models.CharField(default=b'', max_length=22, verbose_name='Organizer Phone', blank=True)),
                ('start_date', models.DateField(verbose_name='Start Date', db_index=True)),
                ('number_of_days', models.PositiveSmallIntegerField(default=1, verbose_name='Number of Days')),
                ('using_tags', models.BooleanField(default=False, verbose_name='Using Tags/Chip Reader')),
                ('use_existing_tags', models.BooleanField(default=True, verbose_name="Use Competitor's Existing Tags")),
                ('distance_unit', models.PositiveSmallIntegerField(default=0, verbose_name='Distance Unit', choices=[(0, 'km'), (1, 'miles')])),
                ('category_format', models.ForeignKey(verbose_name='Category Format', to='core.CategoryFormat')),
            ],
            options={
                'ordering': ['-start_date', 'name'],
                'verbose_name': 'Competition',
                'verbose_name_plural': 'Competitions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence')),
            ],
            options={
                'ordering': ['sequence', 'name'],
                'verbose_name': 'Discipline',
                'verbose_name_plural': 'Disciplines',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventMassStart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('date_time', models.DateTimeField(verbose_name='Date Time', db_index=True)),
                ('event_type', models.PositiveSmallIntegerField(default=0, verbose_name=b'Event Type', choices=[(0, 'Mass Start'), (1, 'Time Trial')])),
                ('competition', models.ForeignKey(to='core.Competition')),
            ],
            options={
                'verbose_name': 'Mass Start Event',
                'verbose_name_plural': 'Mass Starts Event',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LicenseHolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_name', models.CharField(max_length=64, verbose_name='Last Name', db_index=True)),
                ('first_name', models.CharField(max_length=64, verbose_name='First Name', db_index=True)),
                ('gender', models.PositiveSmallIntegerField(default=0, choices=[(0, 'Men'), (1, 'Women')])),
                ('date_of_birth', models.DateField()),
                ('city', models.CharField(default=b'', max_length=64, verbose_name='City', blank=True)),
                ('state_prov', models.CharField(default=b'', max_length=64, verbose_name='State/Prov', blank=True)),
                ('nationality', models.CharField(default=b'', max_length=64, verbose_name='Nationality', blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('uci_code', models.CharField(default=b'', max_length=11, verbose_name='UCI Code', db_index=True, blank=True)),
                ('license_code', models.CharField(max_length=32, unique=True, null=True, verbose_name='License Code')),
                ('existing_bib', models.PositiveSmallIntegerField(db_index=True, null=True, verbose_name='Existing Bib', blank=True)),
                ('existing_tag', models.CharField(max_length=36, unique=True, null=True, verbose_name='Existing Tag', blank=True)),
                ('existing_tag2', models.CharField(max_length=36, unique=True, null=True, verbose_name='Existing Tag2', blank=True)),
                ('suspended', models.BooleanField(default=False, db_index=True, verbose_name='Suspended')),
                ('active', models.BooleanField(default=True, db_index=True, verbose_name='Active')),
                ('search_text', models.CharField(default=b'', max_length=256, db_index=True, blank=True)),
            ],
            options={
                'ordering': ['search_text'],
                'verbose_name': 'LicenseHolder',
                'verbose_name_plural': 'LicenseHolders',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NumberSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence', db_index=True)),
            ],
            options={
                'ordering': ['sequence'],
                'verbose_name': 'Number Set',
                'verbose_name_plural': 'Number Sets',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NumberSetEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bib', models.PositiveSmallIntegerField(verbose_name='Bib', db_index=True)),
                ('license_holder', models.ForeignKey(to='core.LicenseHolder')),
                ('number_set', models.ForeignKey(to='core.NumberSet')),
            ],
            options={
                'verbose_name': 'NumberSetEntry',
                'verbose_name_plural': 'NumberSetEntries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.PositiveSmallIntegerField(default=110, verbose_name='Role', choices=[('Team', ((110, 'Competitor'), (120, 'Manager'), (130, 'Coach'), (140, 'Doctor'), (150, 'Paramedical Asst.'), (160, 'Mechanic'), (170, 'Driver'), (199, 'Team Staff'))), ('Official', ((210, 'Commissaire'), (220, 'Timer'), (230, 'Announcer'), (240, 'Radio Operator'), (250, 'Para Classifier'), (299, 'Official Staff'))), ('Organizer', ((310, 'Administrator'), (320, 'Mechanic'), (330, 'Driver'), (399, 'Organizer Staff')))])),
                ('preregistered', models.BooleanField(default=False, verbose_name='Preregistered')),
                ('registration_timestamp', models.DateTimeField(auto_now_add=True)),
                ('bib', models.PositiveSmallIntegerField(db_index=True, null=True, verbose_name='Bib', blank=True)),
                ('tag', models.CharField(max_length=36, null=True, verbose_name='Tag', blank=True)),
                ('tag2', models.CharField(max_length=36, null=True, verbose_name='Tag2', blank=True)),
                ('signature', models.TextField(default=b'', verbose_name='Signature', blank=True)),
                ('paid', models.BooleanField(default=False, verbose_name='Paid')),
                ('confirmed', models.BooleanField(default=False, verbose_name='Confirmed')),
                ('note', models.TextField(default=b'', verbose_name='Note', blank=True)),
                ('category', models.ForeignKey(blank=True, to='core.Category', null=True)),
                ('competition', models.ForeignKey(to='core.Competition')),
                ('license_holder', models.ForeignKey(to='core.LicenseHolder')),
            ],
            options={
                'ordering': ['license_holder__search_text'],
                'verbose_name': 'Participant',
                'verbose_name_plural': 'Participants',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RaceClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence')),
            ],
            options={
                'ordering': ['sequence', 'name'],
                'verbose_name': 'Race Class',
                'verbose_name_plural': 'Race Classes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SeasonsPass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('sequence', models.PositiveSmallIntegerField(default=0, verbose_name='Sequence', db_index=True)),
            ],
            options={
                'ordering': ['sequence'],
                'verbose_name': "Season's Pass",
                'verbose_name_plural': "Season's Passes",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SeasonsPassHolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('license_holder', models.ForeignKey(verbose_name='LicenseHolder', to='core.LicenseHolder', unique=True)),
                ('seasons_pass', models.ForeignKey(verbose_name="Season's Pass", to='core.SeasonsPass')),
            ],
            options={
                'ordering': ['license_holder__search_text'],
                'verbose_name': "Season's Pass Holder",
                'verbose_name_plural': "Season's Pass Holders",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SystemInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag_template', models.CharField(help_text='Template for generating EPC RFID tags.', max_length=24, verbose_name='Tag Template')),
                ('rfid_server_host', models.CharField(default=b'localhost', max_length=32, verbose_name='RFID Reader Server Host')),
                ('rfid_server_port', models.PositiveSmallIntegerField(default=50111, verbose_name='RFID Reader Server Port')),
                ('reg_closure_minutes', models.IntegerField(default=-1, help_text='Minutes before race start to close registration for "reg" users.  Use -1 for None.', verbose_name='Reg Closure Minutes')),
            ],
            options={
                'verbose_name': 'SystemInfo',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='Name', db_index=True)),
                ('team_code', models.CharField(db_index=True, max_length=3, verbose_name='Team Code', blank=True)),
                ('team_type', models.PositiveSmallIntegerField(default=0, verbose_name='Type', choices=[(0, 'Club'), (1, 'Regional'), (2, 'Mixed'), (3, 'National'), (4, 'UCI Women'), (5, 'UCI Continental'), (6, 'UCI Pro Continental'), (7, 'UCI Pro')])),
                ('nation_code', models.CharField(default=b'', max_length=3, verbose_name='Nation Code', blank=True)),
                ('active', models.BooleanField(default=True, verbose_name='Active')),
                ('search_text', models.CharField(default=b'', max_length=80, db_index=True, blank=True)),
                ('was_team', models.OneToOneField(related_name='is_now_team', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='core.Team', verbose_name='Was Team')),
            ],
            options={
                'ordering': ['search_text'],
                'verbose_name': 'Team',
                'verbose_name_plural': 'Teams',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeamHint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('effective_date', models.DateField(verbose_name='Effective Date', db_index=True)),
                ('discipline', models.ForeignKey(to='core.Discipline')),
                ('license_holder', models.ForeignKey(to='core.LicenseHolder')),
                ('team', models.ForeignKey(to='core.Team')),
            ],
            options={
                'verbose_name': 'TeamHint',
                'verbose_name_plural': 'TeamHints',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Wave',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('start_offset', core.DurationField.DurationField(default=0, verbose_name='Start Offset')),
                ('distance', models.FloatField(null=True, verbose_name='Distance', blank=True)),
                ('laps', models.PositiveSmallIntegerField(null=True, verbose_name='Laps', blank=True)),
                ('minutes', models.PositiveSmallIntegerField(null=True, verbose_name='Race Minutes', blank=True)),
                ('categories', models.ManyToManyField(to='core.Category', verbose_name='Categories')),
                ('event', models.ForeignKey(to='core.EventMassStart')),
            ],
            options={
                'ordering': ['start_offset', 'name'],
                'verbose_name': 'Wave',
                'verbose_name_plural': 'Waves',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WaveCallup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField(default=9999, verbose_name='Callup Order', blank=True)),
                ('participant', models.ForeignKey(to='core.Participant')),
                ('wave', models.ForeignKey(to='core.Wave')),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'WaveCallup',
                'verbose_name_plural': 'WaveCallups',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='participant',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='core.Team', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set([('competition', 'category', 'tag'), ('competition', 'category', 'license_holder'), ('competition', 'category', 'tag2'), ('competition', 'category', 'bib')]),
        ),
        migrations.AddField(
            model_name='competition',
            name='discipline',
            field=models.ForeignKey(verbose_name='Discipline', to='core.Discipline'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='number_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Number Set', blank=True, to='core.NumberSet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='race_class',
            field=models.ForeignKey(verbose_name='Race Class', to='core.RaceClass'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='competition',
            name='seasons_pass',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name="Season's Pass", blank=True, to='core.SeasonsPass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='categorynumbers',
            name='competition',
            field=models.ForeignKey(to='core.Competition'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='categoryhint',
            name='discipline',
            field=models.ForeignKey(to='core.Discipline'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='categoryhint',
            name='license_holder',
            field=models.ForeignKey(to='core.LicenseHolder'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='format',
            field=models.ForeignKey(to='core.CategoryFormat'),
            preserve_default=True,
        ),
    ]
