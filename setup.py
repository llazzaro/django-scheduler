#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
 
setup(
    name='django-schedule',
    version='0.5b',
    description='A calendaring app for Django.',
    author='Anthony Robert Hauber',
    author_email='thauber@gmail.com',
    url='http://github.com/thauber/django-schedule/tree/master',
    packages=[
        'schedule',
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
    install_requires=['setuptools', 'vobject', 'python-dateutil'],
    license='BSD',
    test_suite = "schedule.tests",
)
