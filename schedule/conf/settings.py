from builtins import str
from django.utils.translation import ugettext_lazy
from django.core.exceptions import ImproperlyConfigured
from annoying.functions import get_config

fdow_default = 0  # Sunday

# Look for FIRST_DAY_OF_WEEK as a locale setting
fdow = ugettext_lazy('FIRST_DAY_OF_WEEK')
try:
    FIRST_DAY_OF_WEEK = int(str(fdow))
except ValueError:
    # Let's try our settings
    fdow = get_config('FIRST_DAY_OF_WEEK', fdow_default)
    FIRST_DAY_OF_WEEK = int(fdow)
except ValueError:
    raise ImproperlyConfigured("FIRST_DAY_OF_WEEK must be an integer between 0 and 6")

AUTH_USER_MODEL = get_config('AUTH_USER_MODEL')
# whether to display cancelled occurrences
# (if they are displayed then they have a css class "cancelled")
# this controls behaviour of Period.classify_occurrence method
SHOW_CANCELLED_OCCURRENCES = get_config('SHOW_CANCELLED_OCCURRENCES', False)

# Callable used to check if a user has edit permissions to event
# (and occurrence). Used by check_edit_permission decorator
# if ob==None we check permission to add occurrence
CHECK_EVENT_PERM_FUNC = get_config('CHECK_EVENT_PERM_FUNC', None)

if not CHECK_EVENT_PERM_FUNC:
    CHECK_EVENT_PERM_FUNC = get_config('CHECK_PERMISSION_FUNC', None)

if not CHECK_EVENT_PERM_FUNC:
    def check_event_permission(ob, user):
        return user.is_authenticated()

    CHECK_EVENT_PERM_FUNC = check_event_permission

# Callable used to check if a user has edit permissions to calendar
CHECK_CALENDAR_PERM_FUNC = get_config('CHECK_CALENDAR_PERM_FUNC', None)

if not CHECK_CALENDAR_PERM_FUNC:
    def check_calendar_permission(ob, user):
        return user.is_authenticated()

    CHECK_CALENDAR_PERM_FUNC = check_calendar_permission

# Callable used to customize the event list given for a calendar and user
# (e.g. all events on that calendar, those events plus another calendar's events,
# or the events filtered based on user permissions)
# Imports have to be placed within the function body to avoid circular imports
GET_EVENTS_FUNC = get_config('GET_EVENTS_FUNC', None)
if not GET_EVENTS_FUNC:
    def get_events(request, calendar):
        return calendar.event_set.prefetch_related('occurrence_set','rule')

    GET_EVENTS_FUNC = get_events

# URL to redirect to to after an occurrence is canceled
OCCURRENCE_CANCEL_REDIRECT = get_config('OCCURRENCE_CANCEL_REDIRECT', None)
