# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six.moves.builtins import str
from django.utils.translation import ugettext_lazy as _

from schedule.settings import USE_FULLCALENDAR
from schedule.utils import EventListManager


class CalendarManager(models.Manager):
    """
    >>> user1 = User(username='tony')
    >>> user1.save()
    """
    def get_calendar_for_object(self, obj, distinction=''):
        """
        This function gets a calendar for an object.  It should only return one
        calendar.  If the object has more than one calendar related to it (or
        more than one related to it under a distinction if a distinction is
        defined) an AssertionError will be raised.  If none are returned it will
        raise a DoesNotExistError.

        >>> user = User.objects.get(username='tony')
        >>> try:
        ...     Calendar.objects.get_calendar_for_object(user)
        ... except Calendar.DoesNotExist:
        ...     print("failed")
        ...
        failed

        Now if we add a calendar it should return the calendar

        >>> calendar = Calendar(name='My Cal')
        >>> calendar.save()
        >>> calendar.create_relation(user)
        >>> Calendar.objects.get_calendar_for_object(user)
        <Calendar: My Cal>

        Now if we add one more calendar it should raise an AssertionError
        because there is more than one related to it.

        If you would like to get more than one calendar for an object you should
        use get_calendars_for_object (see below).
        >>> calendar = Calendar(name='My 2nd Cal')
        >>> calendar.save()
        >>> calendar.create_relation(user)
        >>> try:
        ...     Calendar.objects.get_calendar_for_object(user)
        ... except AssertionError:
        ...     print("failed")
        ...
        failed
        """
        calendar_list = self.get_calendars_for_object(obj, distinction)
        if len(calendar_list) == 0:
            raise Calendar.DoesNotExist("Calendar does not exist.")
        elif len(calendar_list) > 1:
            raise AssertionError("More than one calendars were found.")
        else:
            return calendar_list[0]

    def get_or_create_calendar_for_object(self, obj, distinction='', name=None):
        """
        >>> user = User(username="jeremy")
        >>> user.save()
        >>> calendar = Calendar.objects.get_or_create_calendar_for_object(user, name = "Jeremy's Calendar")
        >>> calendar.name
        "Jeremy's Calendar"
        """
        try:
            return self.get_calendar_for_object(obj, distinction)
        except Calendar.DoesNotExist:
            if name is None:
                calendar = self.model(name=str(obj))
            else:
                calendar = self.model(name=name)
            calendar.slug = slugify(calendar.name)
            calendar.save()
            calendar.create_relation(obj, distinction)
            return calendar

    def get_calendars_for_object(self, obj, distinction=''):
        """
        This function allows you to get calendars for a specific object

        If distinction is set it will filter out any relation that doesnt have
        that distinction.
        """
        ct = ContentType.objects.get_for_model(obj)
        if distinction:
            dist_q = Q(calendarrelation__distinction=distinction)
        else:
            dist_q = Q()
        return self.filter(dist_q, calendarrelation__content_type=ct, calendarrelation__object_id=obj.id)


@python_2_unicode_compatible
class Calendar(models.Model):
    '''
    This is for grouping events so that batch relations can be made to all
    events.  An example would be a project calendar.

    name: the name of the calendar
    events: all the events contained within the calendar.
    >>> calendar = Calendar(name = 'Test Calendar')
    >>> calendar.save()
    >>> data = {
    ...         'title': 'Recent Event',
    ...         'start': datetime.datetime(2008, 1, 5, 0, 0),
    ...         'end': datetime.datetime(2008, 1, 10, 0, 0)
    ...        }
    >>> event = Event(**data)
    >>> event.save()
    >>> calendar.events.add(event)
    >>> data = {
    ...         'title': 'Upcoming Event',
    ...         'start': datetime.datetime(2008, 1, 1, 0, 0),
    ...         'end': datetime.datetime(2008, 1, 4, 0, 0)
    ...        }
    >>> event = Event(**data)
    >>> event.save()
    >>> calendar.events.add(event)
    >>> data = {
    ...         'title': 'Current Event',
    ...         'start': datetime.datetime(2008, 1, 3),
    ...         'end': datetime.datetime(2008, 1, 6)
    ...        }
    >>> event = Event(**data)
    >>> event.save()
    >>> calendar.events.add(event)
    '''

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    objects = CalendarManager()

    class Meta(object):
        verbose_name = _('calendar')
        verbose_name_plural = _('calendars')

    def __str__(self):
        return self.name

    @property
    def events(self):
        return self.event_set

    def create_relation(self, obj, distinction='', inheritable=True):
        """
        Creates a CalendarRelation between self and obj.

        if Inheritable is set to true this relation will cascade to all events
        related to this calendar.
        """
        CalendarRelation.objects.create_relation(self, obj, distinction, inheritable)

    def get_recent(self, amount=5):
        """
        This shortcut function allows you to get events that have started
        recently.

        amount is the amount of events you want in the queryset. The default is
        5.
        """
        return self.events.order_by('-start').filter(start__lt=timezone.now())[:amount]

    def occurrences_after(self, date=None):
        return EventListManager(self.events.all()).occurrences_after(date)

    def get_absolute_url(self):
        if USE_FULLCALENDAR:
            return reverse('fullcalendar', kwargs={'calendar_slug': self.slug})
        return reverse('calendar_home', kwargs={'calendar_slug': self.slug})


class CalendarRelationManager(models.Manager):
    def create_relation(self, calendar, content_object, distinction='', inheritable=True):
        """
        Creates a relation between calendar and content_object.
        See CalendarRelation for help on distinction and inheritable
        """
        return CalendarRelation.objects.create(
            calendar=calendar,
            distinction=distinction,
            content_object=content_object)


@python_2_unicode_compatible
class CalendarRelation(models.Model):
    '''
    This is for relating data to a Calendar, and possible all of the events for
    that calendar, there is also a distinction, so that the same type or kind of
    data can be related in different ways.  A good example would be, if you have
    calendars that are only visible by certain users, you could create a
    relation between calendars and users, with the distinction of 'visibility',
    or 'ownership'.  If inheritable is set to true, all the events for this
    calendar will inherit this relation.

    calendar: a foreign key relation to a Calendar object.
    content_type: a foreign key relation to ContentType of the generic object
    object_id: the id of the generic object
    content_object: the generic foreign key to the generic object
    distinction: a string representing a distinction of the relation, User could
    have a 'veiwer' relation and an 'owner' relation for example.
    inheritable: a boolean that decides if events of the calendar should also
    inherit this relation

    DISCLAIMER: while this model is a nice out of the box feature to have, it
    may not scale well.  If you use this, keep that in mind.
    '''

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, verbose_name=_("calendar"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField(db_index=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(_("distinction"), max_length=20)
    inheritable = models.BooleanField(_("inheritable"), default=True)

    objects = CalendarRelationManager()

    class Meta(object):
        verbose_name = _('calendar relation')
        verbose_name_plural = _('calendar relations')
        index_together = [('content_type', 'object_id')]

    def __str__(self):
        return '%s - %s' % (self.calendar, self.content_object)
