import importlib
import subprocess
import sys

from django.conf import settings
from django.db import migrations
from django.test import TestCase
from django.test.utils import override_settings


class TestSwappableModels(TestCase):

    def _execute_makemigrations(self):
        popen = subprocess.Popen(
            [
                'python',
                '-m',
                'django',
                'makemigrations',
                'test_project',
                '--settings=tests.test_project.settings'
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=settings.BASE_DIR
        )
        popen.wait()

    def _get_migration_class(self):
        module = importlib.import_module('tests.test_project.migrations.0001_initial')
        return module.Migration

    @override_settings(SCHEDULER_CALENDAR_MODEL='schedule.Calendar', SCHEDULER_EVENT_MODEL='schedule.Event')
    def test_migration(self):
        self._execute_makemigrations()
        migration = self._get_migration_class()
        self.assertTrue(migration.initial)
        creations = [op for op in migration.operations if isinstance(op, migrations.CreateModel)]
        self.assertEqual(len(creations), 3)
        calendar, event, occurrence = creations

        # check migrations.CreateModel(name='CustomCalendar', ...)
        self.assertEqual(calendar.name, 'CustomCalendar')
        self.assertFalse(calendar.options.get('abstract'))
        calendar_fields = dict(calendar.fields)
        self.assertIn('name', calendar_fields)  # parent field
        self.assertIn('color', calendar_fields)  # custom field

        # check migrations.CreateModel(name='CustomEvent', ...)
        self.assertEqual(event.name, 'CustomEvent')
        self.assertFalse(event.options.get('abstract'))
        event_fields = dict(event.fields)
        self.assertIn('title', event_fields)  # parent field
        self.assertIn('last_read_at', event_fields)  # custom field

        # check migrations.CreateModel(name='CustomOccurrence', ...)
        self.assertEqual(occurrence.name, 'CustomOccurrence')
        self.assertFalse(occurrence.options.get('abstract'))
        occurrence_fields = dict(occurrence.fields)
        self.assertIn('title', occurrence_fields)  # parent field
        self.assertIn('is_ready', occurrence_fields)  # custom field
