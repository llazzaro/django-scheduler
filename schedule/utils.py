from builtins import object
from functools import wraps
import pytz
import heapq
from annoying.functions import get_object_or_None
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils import timezone
from schedule.conf.settings import CHECK_EVENT_PERM_FUNC, CHECK_CALENDAR_PERM_FUNC


class EventListManager(object):
    """
    This class is responsible for doing functions on a list of events. It is
    used to when one has a list of events and wants to access the occurrences
    from these events in as a group
    """

    def __init__(self, events):
        self.events = events

    def occurrences_after(self, after=None, tzinfo=pytz.utc):
        """
        It is often useful to know what the next occurrence is given a list of
        events.  This function produces a generator that yields the
        the most recent occurrence after the date ``after`` from any of the
        events in ``self.events``
        """
        from schedule.models import Occurrence

        if after is None:
            after = timezone.now()
        occ_replacer = OccurrenceReplacer(
            Occurrence.objects.filter(event__in=self.events))
        generators = [event._occurrences_after_generator(after) for event in self.events]
        occurrences = []

        for generator in generators:
            try:
                heapq.heappush(occurrences, (next(generator), generator))
            except StopIteration:
                pass

        while True:
            if len(occurrences) == 0:
                raise StopIteration

            generator = occurrences[0][1]

            try:
                next_occurence = heapq.heapreplace(occurrences, (next(generator), generator))[0]
            except StopIteration:
                next_occurence = heapq.heappop(occurrences)[0]
            yield occ_replacer.get_occurrence(next_occurence)


class OccurrenceReplacer(object):
    """
    When getting a list of occurrences, the last thing that needs to be done
    before passing it forward is to make sure all of the occurrences that
    have been stored in the datebase replace, in the list you are returning,
    the generated ones that are equivalent.  This class makes this easier.
    """

    def __init__(self, persisted_occurrences):
        lookup = [((occ.event, occ.original_start, occ.original_end), occ) for
                  occ in persisted_occurrences]
        self.lookup = dict(lookup)

    def get_occurrence(self, occ):
        """
        Return a persisted occurrences matching the occ and remove it from lookup since it
        has already been matched
        """
        return self.lookup.pop(
            (occ.event, occ.original_start, occ.original_end),
            occ)

    def has_occurrence(self, occ):
        return (occ.event, occ.original_start, occ.original_end) in self.lookup

    def get_additional_occurrences(self, start, end):
        """
        Return persisted occurrences which are now in the period
        """
        return [occ for key, occ in list(self.lookup.items()) if (occ.start < end and occ.end >= start and not occ.cancelled)]


def check_event_permissions(function):
    @wraps(function)
    def decorator(request, *args, **kwargs):
        from schedule.models import Event, Calendar
        user = request.user
        # check event permission
        event = get_object_or_None(Event, pk=kwargs.get('event_id', None))
        allowed = CHECK_EVENT_PERM_FUNC(event, user)
        if not allowed:
            return HttpResponseRedirect(settings.LOGIN_URL)

        # check calendar permissions
        calendar = None
        if event:
            calendar = event.calendar
        elif 'calendar_slug' in kwargs:
            calendar = Calendar.objects.get(slug=kwargs['calendar_slug'])
        allowed = CHECK_CALENDAR_PERM_FUNC(calendar, user)
        if not allowed:
            return HttpResponseRedirect(settings.LOGIN_URL)

        # all checks passed
        return function(request, *args, **kwargs)

    return decorator


def coerce_date_dict(date_dict):
    """
    given a dictionary (presumed to be from request.GET) it returns a tuple
    that represents a date. It will return from year down to seconds until one
    is not found.  ie if year, month, and seconds are in the dictionary, only
    year and month will be returned, the rest will be returned as min. If none
    of the parts are found return an empty tuple.
    """
    keys = ['year', 'month', 'day', 'hour', 'minute', 'second']
    ret_val = {
        'year': 1,
        'month': 1,
        'day': 1,
        'hour': 0,
        'minute': 0,
        'second': 0}
    modified = False
    for key in keys:
        try:
            ret_val[key] = int(date_dict[key])
            modified = True
        except KeyError:
            break
    return modified and ret_val or {}

