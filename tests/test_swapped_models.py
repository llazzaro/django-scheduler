import importlib
import os
import subprocess

from django.conf import settings
from django.db import migrations
from django.test import TestCase
from django.test.utils import override_settings


class TestSwappableModels(TestCase):
    """
    This test verifies that it is possible to install `django-scheduler`
    and then swap its models.
    """
    settings_path = os.path.join(settings.BASE_DIR, 'tests', 'test_project', 'settings.py')
    updated_settings_path = os.path.join(settings.BASE_DIR, 'tests', 'test_project', 'updated_settings.py.tpl')

    def setUp(self):
        super(TestSwappableModels, self).setUp()
        # cleanup any possible leftovers before running
        self._cleanup()
        # for backup purposes
        with open(self.settings_path) as settings_file:
            self.settings_content = settings_file.read()

    def tearDown(self):
        # cleanup leftovers after running
        self._cleanup()
        # reset the settings to their previous value
        with open(self.settings_path, 'w') as settings_file:
            settings_file.write(self.settings_content)
        super(TestSwappableModels, self).tearDown()

    def _cleanup(self):
        """
        Remove possibly generated migration files.
        """
        migration_file = os.path.join(
            settings.BASE_DIR,
            'tests',
            'test_project',
            'migrations',
            '0001_initial.py'
        )
        try:
            os.remove(migration_file)
        except OSError:
            # it's ok
            pass

    def _check_command_return(self, command_name, popen):
        """
        Check bash command return code, and fail if the return
        code is non-zero. It takes a `command_name` argument to
        make the output human-readable, and a `Popen` instance
        in order to inspect it.
        """
        if popen.returncode != 0:
            self.fail(
                'Command {} failed, return code {}\n'
                'stdout: {}\n'
                'sterr: {}\n'.format(
                    command_name,
                    popen.returncode,
                    popen.stdout,
                    popen.stderr
                )
            )

    def _execute_makemigrations(self):
        """
        Execute `python -m django makemigrations test_project --settings=tests.test_project.settings`.
        """
        popen = subprocess.Popen(
            [
                'python',
                '-m',
                'django',
                'makemigrations',
                'test_project',
                '--settings=tests.test_project.settings'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=settings.BASE_DIR
        )
        popen.wait()
        self._check_command_return('makemigrations', popen)

    def _update_settings(self):
        """
        Update settings using the `updated_settings.py.tpl` template.

        N.B.: this is reverted during the tearDown() phase.
        """
        with open(self.settings_path, 'w') as settings_file:
            with open(self.updated_settings_path) as updated_settings_file:
                settings_file.write(updated_settings_file.read())

    def _check_makemigrations(self):
        """
        Verify that the test_project doesn't need migrations by using the `--check`
        options of `makemigrations` command.
        """
        popen = subprocess.Popen(
            [
                'python',
                '-m',
                'django',
                'makemigrations',
                'test_project',
                '--settings=tests.test_project.settings',
                '--no-input',
                '--dry-run',
                '--check'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=settings.BASE_DIR
        )
        popen.wait()

        self._check_command_return('makemigrations --check', popen)

    def _get_migration_class(self):
        module = importlib.import_module('tests.test_project.migrations.0001_initial')
        return module.Migration

    @override_settings(SCHEDULER_CALENDAR_MODEL='schedule.Calendar', SCHEDULER_EVENT_MODEL='schedule.Event')
    def test_migration(self):
        # 1st step, execute the migration
        self._execute_makemigrations()
        # 2nd step, update the settings
        self._update_settings()
        # 3rd step, migration check: state should be ok
        self._check_makemigrations()

        # finally verify everything
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
