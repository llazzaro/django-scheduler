from django.contrib.contenttypes import generic
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
import datetime




class EventManager(models.Manager):
    
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
    datetime_of_creation = models.DateTimeField(default = datetime.datetime.now)
    
    objects = EventManager()
    
    def __unicode__(self):
        return '%s: %s-%s' % (
                                self.title,
                                self.start.strftime('%A %b %d, %Y'),
                                self.end.strftime('%A %b %d, %Y'),
                             )
    
    def day(self, in_date):
        '''
        Takes in a date or datetime object and tells how this event relates to 
        that date.
    
        It returns None if the event does not occur on that day at all. It 
        returns -1 if it is the first day this event occurs, it returns 1 if it 
        is the last day this event occurs, and it returns 0 if it occurs on the
        date but is not the first or last day it occurs. It returns 2 if it is 
        both the day this event begins and ends, and it returns None if this
        event does not occur on this day
        
        >>> data = {    
        ...         'title': 'Test', 
        ...         'start': datetime.datetime(2008, 1, 5),
        ...         'end': datetime.datetime(2008, 1, 10)
        ...        }
        >>> Event.objects.all().delete()
        >>> event = Event(**data)
        
        >>> dt = datetime.date(2008,1,5)
        >>> event.day(dt)
        -1
        
        >>> dt = datetime.date(2008,1,7)
        >>> event.day(dt)
        0
        
        >>> dt = datetime.date(2008,1,10)
        >>> event.day(dt)
        1
        
        >>> dt = datetime.date(2008,1,1)
        >>> event.day(dt)
        
        >>> data['end'] = datetime.datetime(2008, 1, 5)
        >>> event = Event(**data)
        >>> dt = datetime.date(2008,1,5)
        >>> event.day(dt)
        2
        '''
        if isinstance(in_date, datetime.datetime):
            in_date = in_date.date()
        
        if self.start.date() == in_date and self.end.date() == in_date:
            return 2
        elif self.start.date() == in_date:
            return -1
        elif self.end.date() == in_date:
            return 1
        elif in_date > self.start.date() and in_date < self.end.date():
            return 0
        return None
    

class Calendar(models.Model):
    '''
    This is for grouping events so that batch relations can be made to all
    events.  An example would be a project calendar.     
    
    name: the name of the calendar
    events: all the events contained within the calendar.
    '''
    
    name = models.CharField(max_length = 200)
    events = models.ManyToManyField(Event)
    
    def __unicode__(self):
        return self.name

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
    distinction = models.CharField(max_length = 20)
    inheritable = models.BooleanField(default=True)
    
    @classmethod
    def create_relation(cls, calendar=None, content_object=None, distinction=None, inheritable=True):
        if content_object is None or calendar is None or distinction is None:
            raise TypeError('create_event_relation requires 3 keyword arguments')
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

class EventRelationManager(models.Manager):
    '''
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
    >>> er = EventRelation.create_relation(user1, event1, 'owner')
    >>> er = EventRelation.create_relation(user2, event1, 'viewer')
    >>> er = EventRelation.create_relation(user1, event2, 'viewer')
    '''
    # Currently not supported because of Django short comings.
    # Multiple level reverse lookups of generic relations appears to be 
    # unsupported.
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
        >>> cr = CalendarRelation.create_relation(calendar, user, 'viewer', True)
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
        print Event.objects.filter(inherit_q)
        print Event.objects.filter(event_q)
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
    distinction = models.CharField(max_length = 20)
    
    objects = EventRelationManager()
    
    def __unicode__(self):
        return '%s(%s)-%s' % (self.event.title, self.distinction, self.content_object)
    
    @classmethod
    def create_relation(cls, content_object=None, event=None, distinction=None):
        if content_object is None or event is None or distinction is None:
            raise TypeError('create_event_relation requires 3 keyword arguments')
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

    
"""
import datetime
from scheduling.models import EventManager
test = True

#testing utility functions on manager event



em = EventManager()
em._minimize_time(datetime.datetime(2008,1,1,3,4))
test = test and _==datetime.datetime(2008,1,1,0,0)

print test

dt1 = datetime.datetime(2008,1,1,0,0)
dt2 = datetime.datetime(2008,2,1,0,0)
dt3 = datetime.datetime(2008,1,2,0,0)
dt4 = datetime.datetime(2007,12,31,0,0)

"""


    
    