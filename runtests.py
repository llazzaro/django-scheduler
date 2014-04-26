#!/usr/bin/env python
from django.conf import settings
settings.configure(
    INSTALLED_APPS=('schedule', 'django.contrib.contenttypes', 'django.contrib.auth'),
    DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3'}
    })

from django.test.utils import setup_test_environment
setup_test_environment()

from django.core.management import call_command
call_command('test', 'schedule')
