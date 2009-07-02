import datetime
import heapq
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.conf import settings
from schedule.conf.settings import CHECK_PERMISSION_FUNC

class EventListManager(object):
    """
    This class is responsible for doing functions on a list of events. It is
    used to when one has a list of events and wants to access the occurrences
    from these events in as a group
    """
    def __init__(self, events):
        self.events = events

    def occurrences_after(self, after=None):
        """
        It is often useful to know what the next occurrence is given a list of
        events.  This function produces a generator that yields the
        the most recent occurrence after the date ``after`` from any of the
        events in ``self.events``
        """
        from schedule.models import Occurrence
        if after is None:
            after = datetime.datetime.now()
        occ_replacer = OccurrenceReplacer(
            Occurrence.objects.filter(event__in = self.events))
        generators = [event._occurrences_after_generator(after) for event in self.events]
        occurrences = []

        for generator in generators:
            try:
                heapq.heappush(occurrences, (generator.next(), generator))
            except StopIteration:
                pass

        while True:
            if len(occurrences) == 0: raise StopIteration

            generator=occurrences[0][1]

            try:
                next = heapq.heapreplace(occurrences, (generator.next(), generator))[0]
            except StopIteration:
                next = heapq.heappop(occurrences)[0]
            yield occ_replacer.get_occurrence(next)


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
        return [occ for key,occ in self.lookup.items() if (occ.start < end and occ.end >= start and not occ.cancelled)]


class check_event_permissions(object):

    def __init__(self, f):
        self.f = f
        self.contenttype = ContentType.objects.get(app_label='schedule', model='event')

    def __call__(self, request, *args, **kwargs):
        user = request.user
        object_id = kwargs.get('event_id', None)
        try:
            obj = self.contenttype.get_object_for_this_type(pk=object_id)
        except self.contenttype.model_class().DoesNotExist:
            obj = None
        allowed = CHECK_PERMISSION_FUNC(obj, user)
        if not allowed:
            return HttpResponseRedirect(settings.LOGIN_URL)
        return self.f(request, *args, **kwargs)


def coerce_date_dict(date_dict):
    """
    given a dictionary (presumed to be from request.GET) it returns a tuple
    that represents a date. It will return from year down to seconds until one
    is not found.  ie if year, month, and seconds are in the dictionary, only
    year and month will be returned, the rest will be returned as min. If none
    of the parts are found return an empty tuple.
    """
    keys = ['year', 'month', 'day', 'hour', 'minute', 'second']
    retVal = {
                'year': 1,
                'month': 1,
                'day': 1,
                'hour': 0,
                'minute': 0,
                'second': 0}
    modified = False
    for key in keys:
        try:
            retVal[key] = int(date_dict[key])
            modified = True
        except KeyError:
            break
    return modified and retVal or {}

