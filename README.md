Django Scheduler
========

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/llazzaro/django-scheduler)
[<img src="https://img.shields.io/coveralls/llazzaro/django-scheduler.svg">](https://coveralls.io/r/llazzaro/django-scheduler)
[<img src="https://img.shields.io/pypi/v/django-scheduler.svg">](https://pypi.python.org/pypi/django-scheduler)
[![Documentation Status](https://readthedocs.org/projects/django-scheduler/badge/)](https://django-scheduler.readthedocs.io/)


A calendar app for Django

Information
========

* [Documentation](https://django-scheduler.readthedocs.io/)
* [Wiki](https://github.com/llazzaro/django-scheduler/wiki)
* [Sample Project](https://github.com/llazzaro/django-scheduler-sample)


Installation
========

```bash
pip install django-scheduler
```

Edit your `settings.py`

Add to `INSTALLED_APPS`:

```python
'schedule',
```

Add to `TEMPLATE_CONTEXT_PROCESSORS`:

```python
"django.template.context_processors.request"
```

Static assets
=============

Django Scheduler relies on [jQuery](https://jquery.com/) and
[Bootstrap](https://getbootstrap.com/) to provide its user
interface. If you don't need help with adding these to your Django
project, you can skip the next step where we will show you how to add
them to your Django project.

```bash
npm install -g bower
pip install django-bower
```

edit your `settings.py`

add to `INSTALLED_APPS`:

```python
'djangobower',
```

Add staticfinder to `STATICFILES_FINDERS`:

```
'djangobower.finders.BowerFinder',
```

Specify the path to the components root (you need to use an absolute
path):

```
BOWER_COMPONENTS_ROOT = '/PROJECT_ROOT/components/'
```

Add the following Bower dependencies for scheduler:

```
BOWER_INSTALLED_APPS = (
    'jquery',
    'jquery-ui',
    'bootstrap'
)
```

Last step, install bower dependencies with:

```
./manage.py bower install
```

Remember to execute "python manage.py collectstatic"

Features
========

 * one-time and recurring events
 * calendar exceptions (occurrences changed or cancelled)
 * occurrences accessible through Event API and Period API
 * relations of events to generic objects
 * ready to use, nice user interface
 * view day, week, month, three months and year

Configuration
========

Full Calendar examples
======

![Full calendar](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/scheduler.png)

![Monthly view (static)](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/monthly_view.png)

![Daily view (static)](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/daily.png)

Metrics
========
[![Throughput Graph](https://graphs.waffle.io/llazzaro/django-scheduler/throughput.svg)](https://waffle.io/llazzaro/django-scheduler/metrics)

Optional Settings
========

### FIRST_DAY_OF_WEEK

This setting determines which day of the week your calendar begins on if your locale doesn't already set it. Default is 0, which is Sunday.

### OCCURRENCE_CANCEL_REDIRECT

This setting controls the behavior of `Views.get_next_url`. If set, all calendar modifications will redirect here (unless there is a `next` set in the request.)

### SHOW_CANCELLED_OCCURRENCES

This setting controls the behavior of `Period.classify_occurrence`. If True, then occurrences that have been cancelled will be displayed with a css class of canceled, otherwise they won't appear at all.

Defaults to False

### CHECK_EVENT_PERM_FUNC

This setting controls the callable used to determine if a user has permission to edit an event or occurrence. The callable must take the object (event) and the user and return a boolean.

Default:
```python
    check_edit_permission(ob, user):
        return user.is_authenticated
```

If ob is None, then the function is checking for permission to add new events

### CHECK_CALENDAR_PERM_FUNC

This setting controls the callable used to determine if a user has permission to add, update or delete an events in specific calendar. The callable must take the object (calendar) and the user and return a boolean.

Default:
```python
    check_edit_permission(ob, user):
        return user.is_authenticated
```

### GET_EVENTS_FUNC

This setting controls the callable that gets all events for calendar display. The callable must take the request and the calendar and return a `QuerySet` of events. Modifying this setting allows you to pull events from multiple calendars or to filter events based on permissions

Default:
```python
    get_events(request, calendar):
        return calendar.event_set.all()
```

### SCHEDULER_PREVNEXT_LIMIT_SECONDS

This settings allows to set the upper and lower limit in calendars navigation.
Value is in seconds.

Default (two years):
62208000


Contributing
============

## Tests

To run tests on all supported versions of Django and Python, use `tox`:

```
$ tox
```
