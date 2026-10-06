"""Build recurrence rules from an event's scheduling metadata.

The event supplies parameter properties and callbacks, so custom Event behavior
continues to participate without coupling this module to Django model classes.
"""

from dateutil import rrule
from django.utils import timezone

freq_dict_order = {
    "YEARLY": 0,
    "MONTHLY": 1,
    "WEEKLY": 2,
    "DAILY": 3,
    "HOURLY": 4,
    "MINUTELY": 5,
    "SECONDLY": 6,
}
param_dict_order = {
    "byyearday": 1,
    "bymonth": 1,
    "bymonthday": 2,
    "byweekno": 2,
    "byweekday": 3,
    "byhour": 4,
    "byminute": 5,
    "bysecond": 6,
}


def get_rrule_object(event, tzinfo):
    if event.rule is None:
        return
    params = event._event_params()
    frequency = event.rule.rrule_frequency()
    if timezone.is_naive(event.start):
        dtstart = event.start
    else:
        dtstart = event.start.astimezone(tzinfo).replace(tzinfo=None)

    if event.end_recurring_period is None:
        until = None
    elif timezone.is_naive(event.end_recurring_period):
        until = event.end_recurring_period
    else:
        until = event.end_recurring_period.astimezone(tzinfo).replace(tzinfo=None)

    return rrule.rrule(frequency, dtstart=dtstart, until=until, **params)


def _event_params(event):
    freq_order = freq_dict_order[event.rule.frequency]
    rule_params = event.event_rule_params
    start_params = event.event_start_params
    event_params = {}

    if len(rule_params) == 0:
        return event_params

    for param in rule_params:
        # start date influences rule params
        if (
            param in param_dict_order
            and param_dict_order[param] > freq_order
            and param in start_params
        ):
            sp = start_params[param]
            if sp == rule_params[param] or (
                hasattr(rule_params[param], "__iter__") and sp in rule_params[param]
            ):
                event_params[param] = [sp]
            else:
                event_params[param] = rule_params[param]
        else:
            event_params[param] = rule_params[param]

    return event_params
