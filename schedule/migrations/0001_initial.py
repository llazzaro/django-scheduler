# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=200, verbose_name='slug')),
            ],
            options={
                'verbose_name_plural': 'calendar',
                'verbose_name': 'calendar',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CalendarRelation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('object_id', models.IntegerField()),
                ('distinction', models.CharField(null=True, max_length=20, verbose_name='distinction')),
                ('inheritable', models.BooleanField(default=True, verbose_name='inheritable')),
                ('calendar', models.ForeignKey(to='schedule.Calendar', verbose_name='calendar', on_delete=models.CASCADE)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'calendar relations',
                'verbose_name': 'calendar relation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(help_text='The end time must be later than the start time.', verbose_name='end')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, verbose_name='updated on')),
                ('end_recurring_period', models.DateTimeField(blank=True, null=True, help_text='This date is ignored for one time only events.', verbose_name='end recurring period')),
                ('calendar', models.ForeignKey(blank=True, null=True, to='schedule.Calendar', verbose_name='calendar', on_delete=models.CASCADE)),
                ('creator', models.ForeignKey(blank=True, null=True, related_name='creator', verbose_name='creator', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'events',
                'verbose_name': 'event',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventRelation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('object_id', models.IntegerField()),
                ('distinction', models.CharField(null=True, max_length=20, verbose_name='distinction')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('event', models.ForeignKey(to='schedule.Event', verbose_name='event', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'event relations',
                'verbose_name': 'event relation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Occurrence',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(blank=True, null=True, max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(verbose_name='end')),
                ('cancelled', models.BooleanField(default=False, verbose_name='cancelled')),
                ('original_start', models.DateTimeField(verbose_name='original start')),
                ('original_end', models.DateTimeField(verbose_name='original end')),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, verbose_name='updated on')),
                ('event', models.ForeignKey(to='schedule.Event', verbose_name='event', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'occurrences',
                'verbose_name': 'occurrence',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=32, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('frequency', models.CharField(max_length=10, choices=[('YEARLY', 'Yearly'), ('MONTHLY', 'Monthly'), ('WEEKLY', 'Weekly'), ('DAILY', 'Daily'), ('HOURLY', 'Hourly'), ('MINUTELY', 'Minutely'), ('SECONDLY', 'Secondly')], verbose_name='frequency')),
                ('params', models.TextField(blank=True, null=True, verbose_name='params')),
            ],
            options={
                'verbose_name_plural': 'rules',
                'verbose_name': 'rule',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='rule',
            field=models.ForeignKey(blank=True, null=True, to='schedule.Rule', verbose_name='rule', help_text="Select '----' for a one time only event.", on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
