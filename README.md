Django Scheduler
========

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/llazzaro/django-scheduler?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[<img src="https://img.shields.io/travis/llazzaro/django-scheduler.svg">](https://travis-ci.org/llazzaro/django-scheduler)
[<img src="https://img.shields.io/coveralls/llazzaro/django-scheduler.svg">](https://coveralls.io/r/llazzaro/django-scheduler)
[<img src="https://img.shields.io/pypi/v/django-scheduler.svg">](https://pypi.python.org/pypi/django-scheduler)
[<img src="https://pypip.in/d/django-scheduler/badge.png">](https://pypi.python.org/pypi/django-scheduler)
[<img src="https://pypip.in/license/django-scheduler/badge.png">](https://github.com/llazzaro/django-scheduler/blob/master/LICENSE.txt)


A calendar app for Django

Donate bitcoins to this project or make commits and get tips for it.
If your commit is accepted by a project maintainer and there are bitcoins on its balance, you will get a tip!

        BTC: 1DjMUVGUyJ5aJ5TxGx79K6VWagMSshhftg

[<img src="http://tip4commit.com/projects/882.svg">](http://tip4commit.com/github/llazzaro/django-scheduler)


Information
========

* [Documentation](http://django-scheduler.readthedocs.org/en/latest/)
* [Wiki](https://github.com/llazzaro/django-scheduler/wiki)
* [Sample Project](https://github.com/llazzaro/django-scheduler-sample)


Installation
========

```bash
pip install django-scheduler
```

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

edit your `settings.py`

add to `INSTALLED_APPS`:

```python
'schedule'
```

add to `TEMPLATE_CONTEXT_PROCESSORS`:

```python
"django.core.context_processors.request"
```

Full Calendar examples
======

![Full calendar](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/scheduler.png)

![Monthly view (static)](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/monthly_view.png)

![Daily view (static)](https://raw.githubusercontent.com/llazzaro/django-scheduler-sample/master/daily.png)


Optional Settings
========

### FIRST_DAY_OF_WEEK

This setting determines which day of the week your calendar begins on if your locale doesn't already set it. Default is 0, which is Sunday.

### OCCURRENCE_CANCEL_REDIRECT

This setting controls the behavior of `Views.get_next_url`. If set, all calendar modifications will redirect here (unless there is a `next` set in the request.)

### SHOW_CANCELLED_OCCURRENCES

This setting controls the behavior of `Period.classify_occurence`. If True, then occurences that have been cancelled will be displayed with a css class of canceled, otherwise they won't appear at all.

Defaults to False

### CHECK_PERMISSION_FUNC

_deprecated_

Should be replaced with `CHECK_EVENT_PERM_FUNC`

### CHECK_EVENT_PERM_FUNC

This setting controls the callable used to determine if a user has permission to edit an event or occurrence. The callable must take the object (event) and the user and return a boolean.

Default:
```python
    check_edit_permission(ob, user):
        return user.is_authenticated()
```

If ob is None, then the function is checking for permission to add new events

### CHECK_CALENDAR_PERM_FUNC

This setting controls the callable used to determine if a user has permission to add, update or delete an events in specific calendar. The callable must take the object (calendar) and the user and return a boolean.

Default:
```python
    check_edit_permission(ob, user):
        return user.is_authenticated()
```

### GET_EVENTS_FUNC

This setting controls the callable that gets all events for calendar display. The callable must take the request and the calendar and return a `QuerySet` of events. Modifying this setting allows you to pull events from multiple calendars or to filter events based on permissions

Default:
```python
    get_events(request, calendar):
        return calendar.event_set.all()
```
