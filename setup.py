#!/usr/bin/env python3
from setuptools import setup

with open("README.md") as fp:
    long_description = fp.read()

setup(
    name="django-scheduler",
    version="0.9.2",
    description="A calendaring app for Django.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Leonardo Lazzaro",
    author_email="lazzaroleonardo@gmail.com",
    url="https://github.com/llazzaro/django-scheduler",
    packages=[
        "schedule",
        "schedule.feeds",
        "schedule.models",
        "schedule.migrations",
        "schedule.templatetags",
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
    ],
    python_requires=">=3.5",
    install_requires=[
        "Django>=1.11",
        "python-dateutil>=2.1",
        "pytz>=2013.9",
        "icalendar>=3.8.4",
    ],
    license="BSD",
    test_suite="runtests.runtests",
)
