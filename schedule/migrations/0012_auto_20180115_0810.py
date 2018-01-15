# Generated by Django 2.0.1 on 2018-01-10 08:10

import django.db.models.deletion
from django.db import migrations, models

from schedule import settings


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0011_event_calendar_not_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarrelation',
            name='calendar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.SCHEDULER_CALENDAR_MODEL, verbose_name='calendar'),
        ),
        migrations.AlterField(
            model_name='event',
            name='calendar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.SCHEDULER_CALENDAR_MODEL, verbose_name='calendar'),
        ),
        migrations.AlterField(
            model_name='eventrelation',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.SCHEDULER_EVENT_MODEL, verbose_name='event'),
        ),
        migrations.AlterField(
            model_name='occurrence',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.SCHEDULER_EVENT_MODEL, verbose_name='event'),
        ),
    ]
