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
"""
from schedule.utils import by_month
m = by_month(Event.objects.all())
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
