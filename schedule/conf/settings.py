from annoying.functions import get_config

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

# Callable used to check if a user has edit permissions to occurrence
CHECK_OCCURRENCE_PERM_FUNC = get_config('CHECK_OCCURRENCE_PERM_FUNC', None)

if not CHECK_OCCURRENCE_PERM_FUNC:
    def check_occurrence_permission(ob, user):
        return CHECK_EVENT_PERM_FUNC(ob.event, user)
    CHECK_OCCURRENCE_PERM_FUNC = check_occurrence_permission

CALENDAR_VIEW_PERM = get_config('CALENDAR_VIEW_PERM', False)

# Callable used to check if a user has edit permissions to calendar
CHECK_CALENDAR_PERM_FUNC = get_config('CHECK_CALENDAR_PERM_FUNC', None)

if not CHECK_CALENDAR_PERM_FUNC:
    def check_calendar_permission(ob, user):
        return user.is_authenticated()

    CHECK_CALENDAR_PERM_FUNC = check_calendar_permission

CALENDAR_VIEW_PERM = get_config('CALENDAR_VIEW_PERM', False)

# Callable used to customize the event list given for a calendar and user
# (e.g. all events on that calendar, those events plus another calendar's events,
# or the events filtered based on user permissions)
# Imports have to be placed within the function body to avoid circular imports
GET_EVENTS_FUNC = get_config('GET_EVENTS_FUNC', None)
if not GET_EVENTS_FUNC:
    def get_events(request, calendar):
        return calendar.event_set.prefetch_related('occurrence_set', 'rule')

    GET_EVENTS_FUNC = get_events

# URL to redirect to to after an occurrence is canceled
OCCURRENCE_CANCEL_REDIRECT = get_config('OCCURRENCE_CANCEL_REDIRECT', None)

SCHEDULER_PREVNEXT_LIMIT_SECONDS = get_config('SCHEDULER_PREVNEXT_LIMIT_SECONDS', 62208000)  # two years

USE_FULLCALENDAR = get_config('USE_FULLCALENDAR', False)

#This name is used when a new event is created through selecting in fullcalendar
EVENT_NAME_PLACEHOLDER = get_config('EVENT_NAME_PLACEHOLDER', 'Event Name')