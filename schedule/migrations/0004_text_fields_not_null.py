# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_auto_20160715_0028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarrelation',
            name='distinction',
            field=models.CharField(default='', max_length=20, verbose_name='distinction'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='color_event',
            field=models.CharField(blank=True, default='', max_length=10, verbose_name='Color event'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='description'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='eventrelation',
            name='distinction',
            field=models.CharField(default='', max_length=20, verbose_name='distinction'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='occurrence',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='description'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='occurrence',
            name='title',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='title'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='rule',
            name='params',
            field=models.TextField(blank=True, default='', verbose_name='params'),
            preserve_default=False,
        ),
    ]
