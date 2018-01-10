import importlib

from django.db import migrations
from django.test import TestCase
from django.test.utils import override_settings


class TestSwappableModels(TestCase):
    """
    This test relies entirely on the `test_project` app and the following instruction:

    python -m django makemigrations test_project --settings=tests.test_project.settings

    This instruction is executed in travis.yml, and if you want to execute this test locally
    you'll need to run it by yourself.
    """

    def _get_migration_class(self):
        try:
            module = importlib.import_module('tests.test_project.migrations.0001_initial')
            return module.Migration
        except ImportError:
            raise RuntimeError(self.__doc__.strip())

    @override_settings(SCHEDULER_CALENDAR_MODEL='schedule.Calendar', SCHEDULER_EVENT_MODEL='schedule.Event')
    def test_migration(self):
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
