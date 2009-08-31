h1. Django-schedule

A calendaring/scheduling application, featuring:

 * one-time and recurring events
 * calendar exceptions (occurrences changed or cancelled)
 * occurrences accessible through Event API and Period API
 * relations of events to generic objects
 * ready to use, nice user interface
 * view day, week, month, three months and year
 * project sample which can be launched immediately and reused in your project

See see "wiki page":http://wiki.github.com/thauber/django-schedule for more.

h2. Installation

Download the code; put in into your project's directory or run <pre>python setup.py install</pre> to install system-wide.

REQUIREMENTS: python-vobject (comes with most distribution as a package).

h2. Settings.py

h3. REQUIRED

INSTALLED_APPS - add: 
    'schedule'

TEMPLATE_CONTEXT_PROCESSORS - add:
    "django.core.context_processors.request"

h4. Optional

FIRST_DAY_OF_WEEK

This setting determines which day of the week your calendar begins on if your locale doesn't already set it. Default is 0, which is Sunday.

OCCURRENCE_CANCEL_REDIRECT

This setting controls the behavior of :func:`Views.get_next_url`. If set, all calendar modifications will redirect here (unless there is a `next` set in the request.)

SHOW_CANCELLED_OCCURRENCES

This setting controls the behavior of :func:`Period.classify_occurence`. If True, then occurences that have been cancelled will be displayed with a css class of canceled, otherwise they won't appear at all.

Defaults to False

CHECK_PERMISSION_FUNC

This setting controls the callable used to determine if a user has permission to edit an event or occurance. The callable must take the object and the user and return a boolean. 

Default:
<pre>
    check_edit_permission(ob, user):
        return user.is_authenticated()
</pre>

If ob is None, then the function is checking for permission to add new events

GET_EVENTS_FUNC

This setting controls the callable that gets all events for calendar display. The callable must take the request and the calendar and return a `QuerySet` of events. Modifying this setting allows you to pull events from multiple calendars or to filter events based on permissions

Default:
<pre>
    get_events(request, calendar):
        return calendar.event_set.all()
</pre>
