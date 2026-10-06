"""Generate event occurrences and reconcile persisted exceptions.

The service calls the event's recurrence and occurrence factory methods so
custom Event overrides remain effective. Model classes are supplied by callers
rather than imported here, avoiding a model import cycle.
"""

import datetime

import pytz
from django.utils import timezone

from schedule.utils import OccurrenceReplacer


def _localize_occurrence_start(start, tzinfo, use_naive):
    """Interpret a recurrence's wall time in the query timezone."""
    start = pytz.timezone(str(tzinfo)).localize(start)
    if use_naive:
        return timezone.make_naive(start, tzinfo)
    return start


def _recurring_starts(start_rule, start, end, duration):
    """Include an overlapping prior start and exclude the window's end."""
    starts = []
    closest_start = start_rule.before(start, inc=False)
    if closest_start is not None and closest_start + duration > start:
        starts.append(closest_start)
    in_window = start_rule.between(start, end, inc=True)
    if in_window and in_window[-1] == end:
        in_window.pop()
    starts.extend(in_window)
    return starts


class EventOccurrences:
    def __init__(self, event, occurrence_model):
        self.event = event
        self.occurrence_model = occurrence_model

    def get_occurrences(self, start, end, clear_prefetch=True):
        """
        >>> rule = Rule(frequency = "MONTHLY", name = "Monthly")
        >>> rule.save()
        >>> event = Event(rule=rule, start=datetime.datetime(2008,1,1,tzinfo=pytz.utc), end=datetime.datetime(2008,1,2))
        >>> event.rule
        <Rule: Monthly>
        >>> occurrences = event.get_occurrences(datetime.datetime(2008,1,24), datetime.datetime(2008,3,2))
        >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
        ['2008-02-01 00:00:00+00:00 to 2008-02-02 00:00:00+00:00', '2008-03-01 00:00:00+00:00 to 2008-03-02 00:00:00+00:00']

        Ensure that if an event has no rule, that it appears only once.

        >>> event = Event(start=datetime.datetime(2008,1,1,8,0), end=datetime.datetime(2008,1,1,9,0))
        >>> occurrences = event.get_occurrences(datetime.datetime(2008,1,24), datetime.datetime(2008,3,2))
        >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
        []
        """

        # Explanation of clear_prefetch:
        #
        # Periods, and their subclasses like Week, call
        # prefetch_related('occurrence_set') on all events in their
        # purview. This reduces the database queries they make from
        # len()+1 to 2. However, having a cached occurrence_set on the
        # Event model instance can sometimes cause Events to have a
        # different view of the state of occurrences than the Period
        # managing them.
        #
        # E.g., if you create an unsaved occurrence, move it to a
        # different time [which saves the event], keep a reference to
        # the moved occurrence, & refetch all occurrences from the
        # Period without clearing the prefetch cache, you'll end up
        # with two Occurrences for the same event but different moved
        # states. It's a complicated scenario, but can happen. (See
        # tests/test_occurrence.py#test_moved_occurrences, which caught
        # this bug in the first place.)
        #
        # To prevent this, we clear the select_related cache by default
        # before we call an event's get_occurrences, but allow Period
        # to override this cache clear since it already fetches all
        # occurrence_sets via prefetch_related in its get_occurrences.
        if clear_prefetch:
            self.event.refresh_from_db()

        persisted_occurrences = self.event.occurrence_set.all()
        occ_replacer = OccurrenceReplacer(persisted_occurrences)
        occurrences = self.event._get_occurrence_list(start, end)
        final_occurrences = []
        for occ in occurrences:
            # replace occurrences with their persisted counterparts
            if occ_replacer.has_occurrence(occ):
                p_occ = occ_replacer.get_occurrence(occ)
                # ...but only if they are within this period
                if p_occ.start < end and p_occ.end >= start:
                    final_occurrences.append(p_occ)
            else:
                final_occurrences.append(occ)
        # then add persisted occurrences which originated outside of this period but now
        # fall within it
        final_occurrences += occ_replacer.get_additional_occurrences(start, end)
        return final_occurrences

    def create_occurrence(self, start, end=None):
        if end is None:
            end = start + (self.event.end - self.event.start)
        return self.occurrence_model(
            event=self.event,
            start=start,
            end=end,
            original_start=start,
            original_end=end,
        )

    def get_occurrence(self, date):
        use_naive = timezone.is_naive(date)
        tzinfo = datetime.timezone.utc
        if timezone.is_naive(date):
            date = timezone.make_aware(date, tzinfo)
        if date.tzinfo:
            tzinfo = date.tzinfo
        rule = self.event.get_rrule_object(tzinfo)
        if rule:
            next_occurrence = rule.after(
                date.astimezone(tzinfo).replace(tzinfo=None), inc=True
            )
            next_occurrence = pytz.timezone(str(tzinfo)).localize(next_occurrence)
        else:
            next_occurrence = self.event.start
        if next_occurrence == date:
            try:
                return self.occurrence_model.objects.get(
                    event=self.event, original_start=date
                )
            except self.occurrence_model.DoesNotExist:
                if use_naive:
                    next_occurrence = timezone.make_naive(next_occurrence, tzinfo)
                return self.event._create_occurrence(next_occurrence)

    def get_occurrence_list(self, start, end):
        """
        Returns a list of occurrences that fall completely or partially inside
        the timespan defined by start (inclusive) and end (exclusive)
        """
        if self.event.rule is None:
            if self.event.start < end and self.event.end > start:
                return [self.event._create_occurrence(self.event.start)]
            return []

        duration = self.event.end - self.event.start
        use_naive = timezone.is_naive(start)
        tzinfo = start.tzinfo or datetime.timezone.utc
        # Limit timespan to recurring period.
        if self.event.end_recurring_period and self.event.end_recurring_period < end:
            end = self.event.end_recurring_period
        start_rule = self.event.get_rrule_object(tzinfo)
        start = start.replace(tzinfo=None)
        if timezone.is_aware(end):
            end = end.astimezone(tzinfo).replace(tzinfo=None)

        occurrences = []
        for occurrence_start in self.event._recurring_starts(
            start_rule, start, end, duration
        ):
            occurrence_start = _localize_occurrence_start(
                occurrence_start, tzinfo, use_naive
            )
            occurrence = self.event._create_occurrence(
                occurrence_start, occurrence_start + duration
            )
            if occurrence not in occurrences:
                occurrences.append(occurrence)
        return occurrences

    def occurrences_after_generator(self, after=None):
        """
        returns a generator that produces unpresisted occurrences after the
        datetime ``after``. (Optionally) This generator will return up to
        ``max_occurrences`` occurrences or has reached ``self.event.end_recurring_period``, whichever is smallest.
        """

        tzinfo = datetime.timezone.utc
        if after is None:
            after = timezone.now()
        elif not timezone.is_naive(after):
            tzinfo = after.tzinfo
        rule = self.event.get_rrule_object(tzinfo)
        if rule is None:
            if self.event.end > after:
                yield self.event._create_occurrence(self.event.start, self.event.end)
            return
        date_iter = iter(rule)
        difference = self.event.end - self.event.start
        loop_counter = 0
        for o_start in date_iter:
            o_start = pytz.timezone(str(tzinfo)).localize(o_start)
            o_end = o_start + difference
            if o_end > after:
                yield self.event._create_occurrence(o_start, o_end)

            loop_counter += 1

    def occurrences_after(self, after=None, max_occurrences=None):
        """
        returns a generator that produces occurrences after the datetime
        ``after``.  Includes all of the persisted Occurrences. (Optionally) This generator will return up to
        ``max_occurrences`` occurrences or has reached ``self.event.end_recurring_period``, whichever is smallest.
        """
        if after is None:
            after = timezone.now()
        occ_replacer = OccurrenceReplacer(self.event.occurrence_set.all())
        generator = self.event._occurrences_after_generator(after)
        trickies = list(
            self.event.occurrence_set.filter(
                original_start__lte=after, start__gte=after
            ).order_by("start")
        )
        for index, nxt in enumerate(generator):
            if max_occurrences and index > max_occurrences - 1:
                break
            if len(trickies) > 0 and (nxt is None or nxt.start > trickies[0].start):
                yield trickies.pop(0)
            yield occ_replacer.get_occurrence(nxt)
