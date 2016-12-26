from __future__ import division, unicode_literals
from django.utils.six import with_metaclass
# -*- coding: utf-8 -*-
from django.conf import settings as django_settings
from dateutil import rrule
import datetime

from django.contrib.contenttypes import fields
from django.db import models
from django.db.models.base import ModelBase
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template.defaultfilters import date
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from schedule.models.rules import Rule
from schedule.models.calendars import Calendar
from schedule.utils import OccurrenceReplacer
from schedule.utils import get_model_bases


class EventManager(models.Manager):
    def get_for_object(self, content_object, distinction=None, inherit=True):
        return EventRelation.objects.get_events_for_object(content_object, distinction, inherit)


@python_2_unicode_compatible
class Event(with_metaclass(ModelBase, *get_model_bases())):
    '''
    This model stores meta data for a date.  You can relate this data to many
    other models.
    '''
    start = models.DateTimeField(_("start"), db_index=True)
    end = models.DateTimeField(_("end"), db_index=True, help_text=_("The end time must be later than the start time."))
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), null=True, blank=True)
    creator = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("creator"),
        related_name='creator')
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_("updated on"), auto_now=True)
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("rule"),
        help_text=_("Select '----' for a one time only event."))
    end_recurring_period = models.DateTimeField(_("end recurring period"), null=True, blank=True, db_index=True,
                                                help_text=_("This date is ignored for one time only events."))
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("calendar"))
    color_event = models.CharField(_("Color event"), null=True, blank=True, max_length=10)
    objects = EventManager()

    class Meta(object):
        verbose_name = _('event')
        verbose_name_plural = _('events')
        app_label = 'schedule'
        index_together = (
            ('start', 'end'),
        )

    def __str__(self):
        return ugettext('%(title)s: %(start)s - %(end)s') % {
            'title': self.title,
            'start': date(self.start, django_settings.DATE_FORMAT),
            'end': date(self.end, django_settings.DATE_FORMAT),
        }

    @property
    def seconds(self):
        return (self.end - self.start).total_seconds()

    @property
    def minutes(self):
        return float(self.seconds) / 60

    @property
    def hours(self):
        return float(self.seconds) / 3600

    def get_absolute_url(self):
        return reverse('event', args=[self.id])

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
            persisted_occurrences = self.occurrence_set.select_related(None).all()
        else:
            persisted_occurrences = self.occurrence_set.all()
        occ_replacer = OccurrenceReplacer(persisted_occurrences)
        occurrences = self._get_occurrence_list(start, end)
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

    def get_rrule_object(self, tzinfo):
        if self.rule is not None:
            params = self.rule.get_params()
            frequency = self.rule.rrule_frequency()
            if timezone.is_naive(self.start):
                dtstart = self.start
            else:
                dtstart = tzinfo.normalize(self.start).replace(tzinfo=None)

            return rrule.rrule(frequency, dtstart=dtstart, **params)

    def _create_occurrence(self, start, end=None):
        if end is None:
            end = start + (self.end - self.start)
        return Occurrence(event=self, start=start, end=end, original_start=start, original_end=end)

    def get_occurrence(self, date):
        use_naive = timezone.is_naive(date)
        tzinfo = timezone.utc
        if timezone.is_naive(date):
            date = timezone.make_aware(date, timezone.utc)
        if date.tzinfo:
            tzinfo = date.tzinfo
        rule = self.get_rrule_object(tzinfo)
        if rule:
            next_occurrence = rule.after(tzinfo.normalize(date).replace(tzinfo=None), inc=True)
            next_occurrence = tzinfo.localize(next_occurrence)
        else:
            next_occurrence = self.start
        if next_occurrence == date:
            try:
                return Occurrence.objects.get(event=self, original_start=date)
            except Occurrence.DoesNotExist:
                if use_naive:
                    next_occurrence = timezone.make_naive(next_occurrence, tzinfo)
                return self._create_occurrence(next_occurrence)

    def _get_occurrence_list(self, start, end):
        """
        returns a list of occurrences for this event from start to end.
        """
        difference = (self.end - self.start)
        if self.rule is not None:
            use_naive = timezone.is_naive(start)

            # Use the timezone from the start date
            tzinfo = timezone.utc
            if start.tzinfo:
                tzinfo = start.tzinfo

            occurrences = []
            if self.end_recurring_period and self.end_recurring_period < end:
                end = self.end_recurring_period

            rule = self.get_rrule_object(tzinfo)
            start = (start - difference).replace(tzinfo=None)
            end = (end - difference)
            if timezone.is_aware(end):
                end = tzinfo.normalize(end).replace(tzinfo=None)
            o_starts = []
            o_starts.append(rule.between(start, end, inc=True))
            o_starts.append(rule.between(start - (difference // 2), end - (difference // 2), inc=True))
            o_starts.append(rule.between(start - difference, end - difference, inc=True))
            for occ in o_starts:
                for o_start in occ:
                    o_start = tzinfo.localize(o_start)
                    if use_naive:
                        o_start = timezone.make_naive(o_start, tzinfo)
                    o_end = o_start + difference
                    occurrence = self._create_occurrence(o_start, o_end)
                    if occurrence not in occurrences:
                        occurrences.append(occurrence)
            return occurrences
        else:
            # check if event is in the period
            if self.start < end and self.end > start:
                return [self._create_occurrence(self.start)]
            else:
                return []

    def _occurrences_after_generator(self, after=None):
        """
        returns a generator that produces unpresisted occurrences after the
        datetime ``after``. (Optionally) This generator will return up to
        ``max_occurences`` occurrences or has reached ``self.end_recurring_period``, whichever is smallest.
        """

        tzinfo = timezone.utc
        if after is None:
            after = timezone.now()
        elif not timezone.is_naive(after):
            tzinfo = after.tzinfo
        rule = self.get_rrule_object(tzinfo)
        if rule is None:
            if self.end > after:
                yield self._create_occurrence(self.start, self.end)
            return
        date_iter = iter(rule)
        difference = self.end - self.start
        loop_counter = 0
        for o_start in date_iter:
            o_start = tzinfo.localize(o_start)
            if self.end_recurring_period and self.end_recurring_period and o_start > self.end_recurring_period:
                break
            o_end = o_start + difference
            if o_end > after:
                yield self._create_occurrence(o_start, o_end)

            loop_counter += 1

    def occurrences_after(self, after=None, max_occurences=None):
        """
        returns a generator that produces occurrences after the datetime
        ``after``.  Includes all of the persisted Occurrences. (Optionally) This generator will return up to
        ``max_occurences`` occurrences or has reached ``self.end_recurring_period``, whichever is smallest.
        """
        if after is None:
            after = timezone.now()
        occ_replacer = OccurrenceReplacer(self.occurrence_set.all())
        generator = self._occurrences_after_generator(after)
        trickies = list(self.occurrence_set.filter(original_start__lte=after, start__gte=after).order_by('start'))
        for index, nxt in enumerate(generator):
            if max_occurences and index > max_occurences - 1:
                break
            if (len(trickies) > 0 and (nxt is None or nxt.start > trickies[0].start)):
                yield trickies.pop(0)
            yield occ_replacer.get_occurrence(nxt)


class EventRelationManager(models.Manager):
    '''
    >>> import datetime
    >>> EventRelation.objects.all().delete()
    >>> CalendarRelation.objects.all().delete()
    >>> data = {
    ...         'title': 'Test1',
    ...         'start': datetime.datetime(2008, 1, 1),
    ...         'end': datetime.datetime(2008, 1, 11)
    ...        }
    >>> Event.objects.all().delete()
    >>> event1 = Event(**data)
    >>> event1.save()
    >>> data['title'] = 'Test2'
    >>> event2 = Event(**data)
    >>> event2.save()
    >>> user1 = User(username='alice')
    >>> user1.save()
    >>> user2 = User(username='bob')
    >>> user2.save()
    >>> event1.create_relation(user1, 'owner')
    >>> event1.create_relation(user2, 'viewer')
    >>> event2.create_relation(user1, 'viewer')
    '''
    # Currently not supported
    # Multiple level reverse lookups of generic relations appears to be
    # unsupported in Django, which makes sense.
    #
    # def get_objects_for_event(self, event, model, distinction=None):
    #     '''
    #     returns a queryset full of instances of model, if it has an EventRelation
    #     with event, and distinction
    #     >>> event = Event.objects.get(title='Test1')
    #     >>> EventRelation.objects.get_objects_for_event(event, User, 'owner')
    #     [<User: alice>]
    #     >>> EventRelation.objects.get_objects_for_event(event, User)
    #     [<User: alice>, <User: bob>]
    #     '''
    #     if distinction:
    #         dist_q = Q(eventrelation__distinction = distinction)
    #     else:
    #         dist_q = Q()
    #     ct = ContentType.objects.get_for_model(model)
    #     return model.objects.filter(
    #         dist_q,
    #         eventrelation__content_type = ct,
    #         eventrelation__event = event
    #     )

    def get_events_for_object(self, content_object, distinction=None, inherit=True):
        '''
        returns a queryset full of events, that relate to the object through, the
        distinction

        If inherit is false it will not consider the calendars that the events
        belong to. If inherit is true it will inherit all of the relations and
        distinctions that any calendar that it belongs to has, as long as the
        relation has inheritable set to True.  (See Calendar)

        >>> event = Event.objects.get(title='Test1')
        >>> user = User.objects.get(username = 'alice')
        >>> EventRelation.objects.get_events_for_object(user, 'owner', inherit=False)
        [<Event: Test1: Tuesday, Jan. 1, 2008-Friday, Jan. 11, 2008>]

        If a distinction is not declared it will not vet the relations based on
        distinction.
        >>> EventRelation.objects.get_events_for_object(user, inherit=False)
        [<Event: Test1: Tuesday, Jan. 1, 2008-Friday, Jan. 11, 2008>, <Event: Test2: Tuesday, Jan. 1, 2008-Friday, Jan. 11, 2008>]

        Now if there is a Calendar
        >>> calendar = Calendar(name = 'MyProject')
        >>> calendar.save()

        And an event that belongs to that calendar
        >>> event = Event.objects.get(title='Test2')
        >>> calendar.events.add(event)

        If we relate this calendar to some object with inheritable set to true,
        that relation will be inherited
        >>> user = User.objects.get(username='bob')
        >>> cr = calendar.create_relation(user, 'viewer', True)
        >>> EventRelation.objects.get_events_for_object(user, 'viewer')
        [<Event: Test1: Tuesday, Jan. 1, 2008-Friday, Jan. 11, 2008>, <Event: Test2: Tuesday, Jan. 1, 2008-Friday, Jan. 11, 2008>]
        '''
        ct = ContentType.objects.get_for_model(type(content_object))
        if distinction:
            dist_q = Q(eventrelation__distinction=distinction)
            cal_dist_q = Q(calendar__calendarrelation__distinction=distinction)
        else:
            dist_q = Q()
            cal_dist_q = Q()
        if inherit:
            inherit_q = Q(
                cal_dist_q,
                calendar__calendarrelation__object_id=content_object.id,
                calendar__calendarrelation__content_type=ct,
                calendar__calendarrelation__inheritable=True,
            )
        else:
            inherit_q = Q()
        event_q = Q(dist_q, eventrelation__object_id=content_object.id, eventrelation__content_type=ct)
        return Event.objects.filter(inherit_q | event_q)

    def create_relation(self, event, content_object, distinction=None):
        """
        Creates a relation between event and content_object.
        See EventRelation for help on distinction.
        """
        er = EventRelation(
            event=event,
            distinction=distinction,
            content_object=content_object
        )
        er.save()
        return er


@python_2_unicode_compatible
class EventRelation(with_metaclass(ModelBase, *get_model_bases())):
    '''
    This is for relating data to an Event, there is also a distinction, so that
    data can be related in different ways.  A good example would be, if you have
    events that are only visible by certain users, you could create a relation
    between events and users, with the distinction of 'visibility', or
    'ownership'.

    event: a foreign key relation to an Event model.
    content_type: a foreign key relation to ContentType of the generic object
    object_id: the id of the generic object
    content_object: the generic foreign key to the generic object
    distinction: a string representing a distinction of the relation, User could
    have a 'viewer' relation and an 'owner' relation for example.

    DISCLAIMER: while this model is a nice out of the box feature to have, it
    may not scale well.  If you use this keep that in mind.
    '''
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("event"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    content_object = fields.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(_("distinction"), max_length=20, null=True)

    objects = EventRelationManager()

    class Meta(object):
        verbose_name = _("event relation")
        verbose_name_plural = _("event relations")
        app_label = 'schedule'

    def __str__(self):
        return '%s(%s)-%s' % (self.event.title, self.distinction, self.content_object)


@python_2_unicode_compatible
class Occurrence(with_metaclass(ModelBase, *get_model_bases())):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("event"))
    title = models.CharField(_("title"), max_length=255, blank=True, null=True)
    description = models.TextField(_("description"), blank=True, null=True)
    start = models.DateTimeField(_("start"), db_index=True)
    end = models.DateTimeField(_("end"), db_index=True)
    cancelled = models.BooleanField(_("cancelled"), default=False)
    original_start = models.DateTimeField(_("original start"))
    original_end = models.DateTimeField(_("original end"))
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_("updated on"), auto_now=True)

    class Meta(object):
        verbose_name = _("occurrence")
        verbose_name_plural = _("occurrences")
        app_label = 'schedule'
        index_together = (
            ('start', 'end'),
        )

    def __init__(self, *args, **kwargs):
        super(Occurrence, self).__init__(*args, **kwargs)
        if self.title is None and self.event_id:
            self.title = self.event.title
        if self.description is None and self.event_id:
            self.description = self.event.description

    def moved(self):
        return self.original_start != self.start or self.original_end != self.end

    moved = property(moved)

    def move(self, new_start, new_end):
        self.start = new_start
        self.end = new_end
        self.save()

    def cancel(self):
        self.cancelled = True
        self.save()

    def uncancel(self):
        self.cancelled = False
        self.save()

    @property
    def seconds(self):
        return (self.end - self.start).total_seconds()

    @property
    def minutes(self):
        return float(self.seconds) / 60

    @property
    def hours(self):
        return float(self.seconds) / 3600

    def get_absolute_url(self):
        if self.pk is not None:
            return reverse('occurrence', kwargs={'occurrence_id': self.pk,
                                                 'event_id': self.event.id})
        return reverse('occurrence_by_date', kwargs={
            'event_id': self.event.id,
            'year': self.start.year,
            'month': self.start.month,
            'day': self.start.day,
            'hour': self.start.hour,
            'minute': self.start.minute,
            'second': self.start.second,
        })

    def get_cancel_url(self):
        if self.pk is not None:
            return reverse('cancel_occurrence', kwargs={'occurrence_id': self.pk,
                                                        'event_id': self.event.id})
        return reverse('cancel_occurrence_by_date', kwargs={
            'event_id': self.event.id,
            'year': self.start.year,
            'month': self.start.month,
            'day': self.start.day,
            'hour': self.start.hour,
            'minute': self.start.minute,
            'second': self.start.second,
        })

    def get_edit_url(self):
        if self.pk is not None:
            return reverse('edit_occurrence', kwargs={'occurrence_id': self.pk,
                                                      'event_id': self.event.id})
        return reverse('edit_occurrence_by_date', kwargs={
            'event_id': self.event.id,
            'year': self.start.year,
            'month': self.start.month,
            'day': self.start.day,
            'hour': self.start.hour,
            'minute': self.start.minute,
            'second': self.start.second,
        })

    def __str__(self):
        return ugettext("%(start)s to %(end)s") % {
            'start': date(self.start, django_settings.DATE_FORMAT),
            'end': date(self.end, django_settings.DATE_FORMAT)
        }

    def __lt__(self, other):
        return self.end < other.end

    def __eq__(self, other):
        return (isinstance(other, Occurrence) and
                self.original_start == other.original_start and
                self.original_end == other.original_end)
