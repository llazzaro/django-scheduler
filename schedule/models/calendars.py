# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template.defaultfilters import slugify
import datetime
from dateutil import rrule
from schedule.utils import EventListManager

class CalendarManager(models.Manager):
    """
    >>> user1 = User(username='tony')
    >>> user1.save()
    """
    def get_calendar_for_object(self, obj, distinction=None):
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
        ...     print "failed"
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
        ...     print "failed"
        ...
        failed
        """
        calendar_list = self.get_calendars_for_object(obj, distinction)
        if len(calendar_list) == 0:
            raise Calendar.DoesNotExist, "Calendar does not exist."
        elif len(calendar_list) > 1:
            raise AssertionError, "More than one calendars were found."
        else:
            return calendar_list[0]

    def get_or_create_calendar_for_object(self, obj, distinction = None, name = None):
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
                calendar = Calendar(name = unicode(obj))
            else:
                calendar = Calendar(name = name)
            calendar.slug = slugify(calendar.name)
            calendar.save()
            calendar.create_relation(obj, distinction)
            return calendar

    def get_calendars_for_object(self, obj, distinction = None):
        """
        This function allows you to get calendars for a specific object

        If distinction is set it will filter out any relation that doesnt have
        that distinction.
        """
        ct = ContentType.objects.get_for_model(type(obj))
        if distinction:
            dist_q = Q(calendarrelation__distinction=distinction)
        else:
            dist_q = Q()
        return self.filter(dist_q, Q(calendarrelation__object_id=obj.id, calendarrelation__content_type=ct))

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

    name = models.CharField(_("name"), max_length = 200)
    slug = models.SlugField(_("slug"),max_length = 200)
    objects = CalendarManager()

    class Meta:
        verbose_name = _('calendar')
        verbose_name_plural = _('calendar')
        app_label = 'schedule'

    def __unicode__(self):
        return self.name

    def events(self):
        return self.event_set.all()
    events = property(events)

    def create_relation(self, obj, distinction = None, inheritable = True):
        """
        Creates a CalendarRelation between self and obj.

        if Inheritable is set to true this relation will cascade to all events
        related to this calendar.
        """
        CalendarRelation.objects.create_relation(self, obj, distinction, inheritable)

    def get_recent(self, amount=5, in_datetime = datetime.datetime.now):
        """
        This shortcut function allows you to get events that have started
        recently.

        amount is the amount of events you want in the queryset. The default is
        5.

        in_datetime is the datetime you want to check against.  It defaults to
        datetime.datetime.now
        """
        return self.events.order_by('-start').filter(start__lt=datetime.datetime.now())[:amount]

    def occurrences_after(self, date=None):
        return EventListManager(self.events.all()).occurrences_after(date)

    def get_absolute_url(self):
        return reverse('calendar_home', kwargs={'calendar_slug':self.slug})

    def add_event_url(self):
        return reverse('s_create_event_in_calendar', args=[self.slug])


class CalendarRelationManager(models.Manager):
    def create_relation(self, calendar, content_object, distinction=None, inheritable=True):
        """
        Creates a relation between calendar and content_object.
        See CalendarRelation for help on distinction and inheritable
        """
        ct = ContentType.objects.get_for_model(type(content_object))
        object_id = content_object.id
        cr = CalendarRelation(
            content_type = ct,
            object_id = object_id,
            calendar = calendar,
            distinction = distinction,
            content_object = content_object
        )
        cr.save()
        return cr

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

    calendar = models.ForeignKey(Calendar, verbose_name=_("calendar"))
    content_type = models.ForeignKey(ContentType)
    object_id = models.IntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(_("distinction"), max_length = 20, null=True)
    inheritable = models.BooleanField(_("inheritable"), default=True)

    objects = CalendarRelationManager()

    class Meta:
        verbose_name = _('calendar relation')
        verbose_name_plural = _('calendar relations')
        app_label = 'schedule'

    def __unicode__(self):
        return u'%s - %s' %(self.calendar, self.content_object)
