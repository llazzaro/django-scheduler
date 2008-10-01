import datetime
from django.db.models.query import QuerySet

def by_month(events, month=datetime.date.today()):
    """This function takes an iterable object with events and creates a list of
    tuples in which each element represents a day in the month ``month``."""
    period_range = datetime.timedelta(days=1)
    start, end = _get_month_range(month)
    return _get_periods(events, start, end, period_range)
    
def by_day(events, day=datetime.date.today()):
    period_range = datetime.timedelta(hours=1)
    if isinstance(day, datetime.datetime):
        day = day.date()
    start = datetime.datetime.combine(day, datetime.time.min)
    end = start + datetime.timedelta(days = 1)
    return _get_periods(events, start, end, period_range)

def by_week(events, week=datetime.date.today(), by_hour=False):
    period_range = datettime.timedelta(days=1)
    if by_hour:
        period_range = datettime.timedelta(hours=1)
    start, end = _get_week_range(week)
    return _get_periods(events, start, end, period_range)
    
def _get_week_range(week):
    if isinstance(week, datetime.datetime):
        week = week.date()
    start = datetime.datetime.combine(week, datetime.time.min)
    if week.weekday.isoweekday() < 7:
        start = start - datetime.timedelta(days=week.weekday())
    end = start + datetime.timedelta(days=7)
    return start, end
    
def _get_month_range(month):
    if isinstance(month, datetime.date) or isinstance(month, datetime.datetime):
        year = month.year
        month = month.month
        start = datetime.datetime.min.replace(year=year, month=month)
        if month == 12:
            end = start.replace(month=1, year=year+1)
        else:
            end = start.replace(month=month+1)
    else:
        raise ValueError('`month` must be a datetime.date or datetime.datetime object')
    return start, end
    
def _get_sorted_events(events):
    if isinstance(events, QuerySet):
        return list(events.order_by('start'))
    else:
        events.sort(lambda a,b: cmp(a.start, b.start))
        return events

    
        
        

class Period(object):
    '''
    This class represents a period of time. It has functions for retrieving 
    events within the time period.
    '''
    def __init__(self, events):
        self.start = None
        self.end = None
        self.events = events
        
    def __eq__(self, period):
        return self.start==period.start and self.end==period.end and self.events==period.events
    
    def _get_sorted_events(self, events):
        if isinstance(events, QuerySet):
            return list(events.order_by('start'))
        else:
            events.sort(lambda a,b: cmp(a.start, b.start))
            return events
            
    def classify_event(self, event):
        started = False
        ended = False
        if event.start >= self.end or event.end < self.start:
            return None
        if event.start >= self.start and event.start < self.end:
            started = True
        if event.end >=self.start and event.end < self.end:
            ended = True
        if started and ended:
            return {'event': event, 'class': 1}
        elif started:
            return {'event': event, 'class': 0}
        elif ended:
            return {'event': event, 'class': 3}
        # it existed during this period but it didnt begin or end within it 
        # so it must have just continued
        return {'event': event, 'class': 2}
    
    
    def get_events(self):
        event_dicts = []
        for event in self.events:
            event = self.classify_event(event)
            if event:
                event_dicts.append(event)
        return event_dicts
    
    def _get_periods(events, start, end, period_range):
        events = _get_sorted_events(events)
        periods = {}
        while start < end:
            periods[start]=[]
            period_end = start + period_range
            event_iter = iter(events)
            try:
                event = event_iter.next()
            except StopIteration:
                event = None
            else:
                while event and event.start < period_end:
                    started = False
                    ended = False
                    # if the event is not part of the time frame
                    if event.end < start:
                        events.remove(event)
                    else:
                        # if the event starts in this period
                        if event.start >= start:
                            started = True
                        # if the event ends in the period
                        if event.end < period_end:
                            ended = True
                        if started and ended:
                            periods[start].append((event, 2))
                            events.remove(event)
                        elif started:
                            periods[start].append((event, 1))
                        elif ended:
                            periods[start].append((event, -1))
                            events.remove(event)
                        else:
                            periods[start].append((event, 0))
                    try:
                        event = event_iter.next()
                    except StopIteration:
                        event = None   
            start = period_end
        return periods
        
class Month(Period):
    """
    The month period has functions for retrieving the week periods within this period
    and day periods within the date.
    """
    def __init__(self, events, date=datetime.datetime.now()):
        self.start, self.end = _get_month_range(date)
        self.events = self._get_sorted_events(events)
    
    def get_weeks(self):
        date = self.start
        weeks = []
        while date < self.end:
            #list events to make it only one query
            week = Week(self.events, date)
            weeks.append(week)
            date = week.next_week()
        return weeks
            
    def get_days(self):
        date = self.start
        days = []
        while date < self.end:
            #list events to make it only one query
            day = Day(self.events, date)
            days.append(day)
            date = day.next_day()
        return days
    
    def get_events(self, period_range=datetime.timedelta(days=1)):
        return self._get_events(self.start, self.end, period_range=period_range)
    
    def next_month(self):
        return self.end
        
    def _get_month_range(month):
        if isinstance(month, datetime.date) or isinstance(month, datetime.datetime):
            year = month.year
            month = month.month
            start = datetime.datetime.min.replace(year=year, month=month)
            if month == 12:
                end = start.replace(month=1, year=year+1)
            else:
                end = start.replace(month=month+1)
        else:
            raise ValueError('`month` must be a datetime.date or datetime.datetime object')
        return start, end
    
    def __str__(self):
        return 'Month: %s-%s' % (
            self.start.strftime('%A %b %d, %Y'),
            self.end.strftime('%A %b %d, %Y'),)
    
    def name(self):
        return self.start.strftime('%B')
        
    def year(self):
        return self.start.strftime('%Y')

class Week(Period):
    """
    The Week period that has functions for retrieving Day periods within it
    """
    def __init__(self, events, date=datetime.datetime.now()):
        self.events = self._get_sorted_events(events)
        self.start, self.end = self._get_week_range(date)
        
    def next_week(self):
        return self.end
    
    def get_days(self):
        days = []
        date = self.start
        while date < self.end:
            day = Day(self.events, date)
            days.append(day)
            date = day.next_day()
        return days
    
    def _get_week_range(self, week):
        if isinstance(week, datetime.datetime):
            week = week.date()
        start = datetime.datetime.combine(week, datetime.time.min)
        if week.isoweekday() < 7:
            start = start - datetime.timedelta(days=week.isoweekday())
        end = start + datetime.timedelta(days=7)
        return start, end
    
    def __str__(self):
        return 'Week: %s-%s' % (
            self.start.strftime('%A %b %d, %Y'),
            self.end.strftime('%A %b %d, %Y'),)

class Day(EventManager):
    def __init__(self, events, date=datetime.date.today()):
        self.events = self._get_sorted_events(events)
        if isinstance(date, datetime.datetime):
            date = date.date()
        self.start = datetime.datetime.combine(date, datetime.time.min)
        self.end = self.start + datetime.timedelta(days=1)

    def __str__(self):
        return 'Day: %s-%s' % (
            self.start.strftime('%A %b %d, %Y'),
            self.end.strftime('%A %b %d, %Y'),)
        
    def next_day(self):
        return self.end
        
    def month(self):
        return Month(self.events, self.start)
        
    def week(self):
        return Week(self.events, self.start)
"""
from schedule.utils import Month
m = Month(Event.objects.all())
for w in m.get_weeks():
    print w


items = m.items()
items.sort
mv = [value for key,value in items]
from schedule.utils import by_day
import datetime
d = by_day(Event.objects.all(), day=datetime.date(2008,9,22))
items = d.items()
items.sort
for item in items:
    print '%s: %s' % (item[0], item[1])


"""
