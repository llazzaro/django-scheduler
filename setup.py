#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='django-scheduler',
    version='0.7.1',
    description='A calendaring app for Django.',
    author='Anthony Robert Hauber',
    author_email='thauber@gmail.com',
    url='https://github.com/llazzaro/django-scheduler',
    packages=[
        'schedule',
        'schedule.conf',
        'schedule.feeds',
        'schedule.management',
        'schedule.management.commands',
        'schedule.models',
        'schedule.templatetags',
        'schedule.tests',
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities'],
    install_requires=[
        'Django>=1.5',
        'argparse>=1.2.1',
        'python-dateutil>=2.1',
        'pytz>=2013b',
        'six>=1.3.0',
        'vobject>=0.8.1c',
    ],
    license='BSD',
    test_suite="schedule.tests",
)
