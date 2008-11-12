from django.contrib.contenttypes import generic
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from schedule.periods import Month
from schedule.occurrence import Occurrence
import datetime
from dateutil import rrule


freqs = (   ("YEARLY","Yearly"),
            ("MONTHLY", "Monthly"),
            ("WEEKLY", "Weekly"),
            ("DAILY", "Daily"),
            ("HOURLY", "Hourly"),
            ("MINUTELY", "Minutely"),
            ("SECONDLY", "Secondly"))

class Rule(models.Model):
    """
    This defines a rule by which an event will recur.  This is defined by the
    rrule in the dateutil documentation.

    * name - the human friendly name of this kind of recursion.
    * description - a short description describing this type of recursion.
    * frequency - the base recurrence period
    * param - extra params required to define this type of recursion. The params
      should follow this format:

        param = [rruleparam:value;]*
        rruleparam = see list below
        value = int[,int]*

      The options are: (documentation for these can be found at
      http://labix.org/python-dateutil#head-470fa22b2db72000d7abe698a5783a46b0731b57)
        ** count
        ** bysetpos
        ** bymonth
        ** bymonthday
        ** byyearday
        ** byweekno
        ** byweekday
        ** byhour
        ** byminute
        ** bysecond
        ** byeaster
    """
    name = models.CharField(max_length=32)
    description = models.TextField()
    frequency = models.CharField(choices=freqs, max_length=10)
    params = models.TextField()

    def get_params(self):
        """
        >>> rule = Rule(params = "count:1,2,3;bysecond:1;byminute:1,2,4,5")
        >>> rule.get_params()
        {'count': [1, 2, 3], 'byminute': [1, 2, 4, 5], 'bysecond': [1]}
        """
        params = self.params.split(';')
        param_dict = []
        for param in params:
            param = param.split(':')
            if len(param) == 2:
                param = (str(param[0]), [int(p) for p in param[1].split(',')])
                param_dict.append(param)
        return dict(param_dict)

    def __unicode__(self):
        """Human readable string for Rule"""
        return self.name
    



class EventManager(models.Manager):

    def get_sorted_events(self):
        """
        This retrun a list of the events sorted by start
        """
        return list(self.order_by('start'))

    def get_events_by_month(self, event_date):
        '''
        This takes a date and returns all Events that exist at all in this month.

        More technically it returns the an Event if the if the start of
        the Event is less than (or earlier) than the last day of the month, and
        the end is greater than (or later) than the first day of the month.

        see get_event_by_time_period for more information

        '''
        try:
            event_datetime = _make_date_time(event_date)
        except TypeError:
            raise TypeError("get_events_by_month only takes datetime or date for its argument")
        event_datetime = _minimize_time(event_datetime)
        period_start = event_datetime.replace(day=1)
        period_end = period_start.replace(month=period_start.month)
        return self.get_event_by_time_period(period_start, period_end)

    def get_events_by_date(self, event_date):
        '''
        This takes a date and returns all Events that happen. Date can be a date or
        a datetime.

        date =
        '''
        try:
            event_datetime = _make_date_time(event_date)
        except TypeError:
            raise TypeError("get_events_by_month only takes datetime or date for its argument")
        period_start = _minimize_time(event_datetime)
        period_end = period_start + datetime.timedelta(days=1)
        return self.get_event_by_time_period(period_start, period_end)

    def _minimize_time(self, in_datetime):
        """
        This takes a datetime object and minimizes the time.  It esentially is
        the beginning of the day for the datetime given.

        >>> dt = datetime.datetime(2008,1,1,3,4)
        >>> EventManager()._minimize_time(dt)
        datetime.datetime(2008, 1, 1, 0, 0)

        """
        return datetime.datetime.combine(in_datetime.date(), datetime.time.min)

    def _make_date_time(self, in_datetime):
        """
        This takes in either datetime or date and returns a datetime object, if
        a date is given it returns a datetime object with the date and the
        minimum time.

        >>> dt = datetime.datetime(2008,1,1,1,1)
        >>> EventManager()._make_date_time(dt)
        datetime.datetime(2008, 1, 1, 1, 1)
        >>> d = datetime.date(2008,1,1)
        >>> EventManager()._make_date_time(d)
        datetime.datetime(2008, 1, 1, 0, 0)

        """
        if isinstance(in_datetime, datetime.datetime):
            return in_datetime
        elif isinstance(in_datetime, datetime.date):
            return datetime.datetime.combine(in_datetime, datetime.time.min)
        else:
            raise TypeError("_make_date_time requires a  datetime.date or a datetime.datetime as input.")

    def get_event_by_datetime_period(self, start, end):
        '''
        If the event occurs at any time during the time period it will be returned.
        In other words, if the start date of the event occurs before the end date
        of the date period *and* the end date of the event occurs after the start
        date of the time period.

        # Set up for tests
        >>> data = {
        ...         'title': 'Test',
        ...         'start': datetime.datetime(2008, 1, 5),
        ...         'end': datetime.datetime(2008, 1, 10)
        ...        }
        >>> Event.objects.all().delete()
        >>> event = Event(**data)
        >>> event.save()

        The cases are below
        ===================

        Events that are returned
        ------------------------

        Exists completeley within time period:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            x---------x         <-event
        X====================O  <-time period

        >>> begin = datetime.datetime(2008, 1, 4)
        >>> end = datetime.datetime(2008, 1, 11)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        [<Event: Test: Saturday Jan 05, 2008-Thursday Jan 10, 2008>]

        Surrounds the time period:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~

        x---------------------x <-event
           X===============O    <-time period

        >>> begin = datetime.datetime(2008, 1, 6)
        >>> end = datetime.datetime(2008, 1, 9)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        [<Event: Test: Saturday Jan 05, 2008-Thursday Jan 10, 2008>]

        The start date is within the time period:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            x---------------x   <-event
        X================O      <-time period

        >>> begin = datetime.datetime(2008, 1, 5)
        >>> end = datetime.datetime(2008, 1, 11)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        [<Event: Test: Saturday Jan 05, 2008-Thursday Jan 10, 2008>]

        The end date is within the time period:
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        x-------------x         <-event
            X================O  <-time period

        >>> begin = datetime.datetime(2008, 1, 4)
        >>> end = datetime.datetime(2008, 1, 9)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        [<Event: Test: Saturday Jan 05, 2008-Thursday Jan 10, 2008>]



        Events that are not returned:
        -----------------------------

        Before the time period:
        ~~~~~~~~~~~~~~~~~~~~~~~

        x---x                   <-event
                X============O  <-time period

        >>> begin = datetime.datetime(2008, 1, 11)
        >>> end = datetime.datetime(2008, 1, 12)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        []

        After the time period:
        ~~~~~~~~~~~~~~~~~~~~~~

                         x---x  <-event
        X============O          <-time period

        >>> begin = datetime.datetime(2008, 1, 1)
        >>> end = datetime.datetime(2008, 1, 4)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        []

        Hopefully from above it is obvious that the datetime period is inclusive
        on the start_date and exclusive on the end date

        example:

        Event not returned:
        ~~~~~~~~~~~~~~~~~~~

                         x---x  <-event
        X================O      <-time period

        >>> begin = datetime.datetime(2008, 1, 1)
        >>> end = datetime.datetime(2008, 1, 5)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        []

        Event returned:
        ~~~~~~~~~~~~~~~

        x---x                   <-event
            X================O  <-time period

        >>> begin = datetime.datetime(2008, 1, 10)
        >>> end = datetime.datetime(2008, 1, 15)
        >>> Event.objects.get_event_by_datetime_period(begin, end)
        [<Event: Test: Saturday Jan 05, 2008-Thursday Jan 10, 2008>]

        >>> event.delete()
        '''
        returnset = self.filter(start__lt = end)
        return returnset.filter(end__gte = start)

    def get_for_object(self, content_object, distinction=None, inherit=True):
        return EventRelation.objects.get_events_for_object(content_object, distinction, inherit)

class Event(models.Model):
    '''
    This model stores meta data for a date.  You can relate this data to many
    other models.
    '''
    start = models.DateTimeField()
    end = models.DateTimeField()
    title = models.CharField(max_length = 255)
    description = models.TextField(null = True, blank = True)
    creator = models.ForeignKey(User, null = True)
    created_on = models.DateTimeField(default = datetime.datetime.now)
    end_recurring_period = models.DateTimeField(null = True, blank = True)
    rule = models.ForeignKey(Rule, null = True, blank = True)

    objects = EventManager()

    def __unicode__(self):
        return '%s: %s-%s' % (
                                self.title,
                                self.start.strftime('%A %b %d, %Y'),
                                self.end.strftime('%A %b %d, %Y'),
                             )

    def get_absolute_url(self):
        return reverse('s_event', args=[self.id])

    def create_relation(self, obj, distinction = None):
        """
        Creates a EventRelation between self and obj.
        """
        EventRelation.objects.create_relation(self, obj, distinction)

    def get_occurrences(self, start, end):
        """
        >>> rule = Rule(frequency = "MONTHLY", name = "Monthly")
        >>> rule.save()
        >>> event = Event(rule=rule, start=datetime.datetime(2008,1,1), end=datetime.datetime(2008,1,2))
        >>> event.rule
        <Rule: Monthly>
        >>> occurrences = event.get_occurrences(datetime.datetime(2008,1,24), datetime.datetime(2008,3,2))
        >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
        ['2008-02-01 00:00:00 to 2008-02-02 00:00:00', '2008-03-01 00:00:00 to 2008-03-02 00:00:00']

        Ensure that if an event has no rule and no end_recurring_period defined it appears only once.

        >>> event = Event(start=datetime.datetime(2008,1,1,8,0), end=datetime.datetime(2008,1,1,9,0))
        >>> occurrences = event.get_occurrences(datetime.datetime(2008,1,24), datetime.datetime(2008,3,2))
        >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
        []

        """
        if self.rule is not None:
            params = self.rule.get_params()
            frequency = 'rrule.%s' % self.rule.frequency
            occurrences = []
            if self.end_recurring_period and self.end_recurring_period < end:
                end = self.end_recurring_period
            o_starts = iter(rrule.rrule(eval(frequency), dtstart=self.start, **params))
            try:
                while True:
                    o_start = o_starts.next()
                    o_end = o_start + (self.end - self.start)
                    if o_end >= start:
                        if o_start < end:
                            occurrences.append(Occurrence(self,o_start,o_end))
                        else:
                            break
                return occurrences
            except StopIteration:
                pass
            return occurrences
        else:
            #Check if the period given to get_occurences encompass the event
            if start < self.start and end > self.end:
                return [Occurrence(self, self.start, self.end)]
            else:
                return []

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

    name = models.CharField(max_length = 200)
    events = models.ManyToManyField(Event)

    objects = CalendarManager()

    def __unicode__(self):
        return self.name

    def create_relation(self, obj, distinction = None, inheritable = True):
        """
        Creates a CalendarRelation between self and obj.

        if Inheritable is set to true this relation will cascade to all events
        related to this calendar.
        """
        CalendarRelation.objects.create_relation(self, obj, distinction, inheritable)

    def get_recent_events(self, amount=5, in_datetime = datetime.datetime.now):
        """
        This shortcut function allows you to get events that have started
        recently.

        amount is the amount of events you want in the queryset. The default is
        5.

        in_datetime is the datetime you want to check against.  It defaults to
        datetime.datetime.now
        """
        return self.events.order_by('-start').filter(start__lt=datetime.datetime.now())[:amount]

    def get_upcoming_events(self, amount=5, in_datetime = datetime.datetime.now):
        """
        This shortcut function allows you to get events that will start soon.

        amount is the amount of events you want in the queryset. The default is
        5.

        in_datetime is the datetime you want to check against.  It defaults to
        datetime.datetime.now
        """
        return self.events.order_by('start').filter(start__gt=datetime.datetime.now())[:amount]

    def get_absolute_url(self):
        return reverse('s_calendar', args=[self.id])

    def add_event_url(self):
        return reverse('s_cal_create_event', args=[self.id])

    def get_month(self, date=datetime.datetime.now()):
        return Month(self.events.all(), date)


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

    calendar = models.ForeignKey(Calendar)
    content_type = models.ForeignKey(ContentType)
    object_id = models.IntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(max_length = 20, null=True)
    inheritable = models.BooleanField(default=True)

    objects = CalendarRelationManager()

    def __unicode__(self):
        return '%s - %s' %(self.calendar, self.content_object)

class EventRelationManager(models.Manager):
    '''
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
    # unsupported in Django.
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
        [<Event: Test1: Tuesday Jan 01, 2008-Friday Jan 11, 2008>]

        If a distinction is not declared it will not vet the relations based on
        distinction.
        >>> EventRelation.objects.get_events_for_object(user, inherit=False)
        [<Event: Test1: Tuesday Jan 01, 2008-Friday Jan 11, 2008>, <Event: Test2: Tuesday Jan 01, 2008-Friday Jan 11, 2008>]

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
        [<Event: Test1: Tuesday Jan 01, 2008-Friday Jan 11, 2008>, <Event: Test2: Tuesday Jan 01, 2008-Friday Jan 11, 2008>]
        '''
        ct = ContentType.objects.get_for_model(type(content_object))
        if distinction:
            dist_q = Q(eventrelation__distinction = distinction)
            cal_dist_q = Q(calendar__calendarrelation__distinction = distinction)
        else:
            dist_q = Q()
            cal_dist_q = Q()
        if inherit:
            inherit_q = Q(
                cal_dist_q,
                calendar__calendarrelation__object_id = content_object.id,
                calendar__calendarrelation__content_type = ct,
                calendar__calendarrelation__inheritable = True,
            )
        else:
            inherit_q = Q()
        event_q = Q(dist_q, Q(eventrelation__object_id=content_object.id),Q(eventrelation__content_type=ct))
        return Event.objects.filter(inherit_q|event_q)

    def change_distinction(self, distinction, new_distinction):
        '''
        This function is for change the a group of eventrelations from an old
        distinction to a new one. It should only be used for managerial stuff.
        It is also expensive so it should be used sparingly.
        '''
        for relation in self.filter(distinction = distinction):
            relation.distinction = new_distinction
            relation.save()

    def create_relation(self, event, content_object, distinction=None):
        """
        Creates a relation between event and content_object.
        See EventRelation for help on distinction.
        """
        ct = ContentType.objects.get_for_model(type(content_object))
        object_id = content_object.id
        er = EventRelation(
            content_type = ct,
            object_id = object_id,
            event = event,
            distinction = distinction,
            content_object = content_object
        )
        er.save()
        return er


class EventRelation(models.Model):
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
    have a 'veiwer' relation and an 'owner' relation for example.

    DISCLAIMER: while this model is a nice out of the box feature to have, it
    may not scale well.  If you use this keep that in mind.

    '''
    event = models.ForeignKey(Event)
    content_type = models.ForeignKey(ContentType)
    object_id = models.IntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    distinction = models.CharField(max_length = 20, null=True)

    objects = EventRelationManager()

    def __unicode__(self):
        return '%s(%s)-%s' % (self.event.title, self.distinction, self.content_object)
