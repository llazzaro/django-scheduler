import datetime
from django.db.models.query import QuerySet

from schedule.occurrence import Occurrence

class Period(object):
    '''
    This class represents a period of time. It can return a set of occurrences
    based on its events, and its time period (start and end).s
    '''
    def __init__(self, events, start, end):
        self.start = start
        self.end = end
        self.events = events
        self.occurrences = self._get_sorted_occurrences()

    def __eq__(self, period):
        return self.start==period.start and self.end==period.end and self.events==period.events

    def _get_sorted_occurrences(self):
        occurrences = []
        for event in self.events:
            occurrences += event.get_occurrences(self.start, self.end)
        return sorted(occurrences)

    def classify_occurrence(self, occurrence):
        started = False
        ended = False
        if occurrence.start >= self.start and occurrence.start < self.end:
            started = True
        if occurrence.end >=self.start and occurrence.end< self.end:
            ended = True
        if started and ended:
            return {'occurrence': occurrence, 'class': 1}
        elif started:
            return {'occurrence': occurrence, 'class': 0}
        elif ended:
            return {'occurrence': occurrence, 'class': 3}
        # it existed during this period but it didnt begin or end within it
        # so it must have just continued
        return {'occurrence': occurrence, 'class': 2}

    def get_occurrence_partials(self):
        occurrence_dicts = []
        for occurrence in self.occurrences:
            occurrence = self.classify_occurrence(occurrence)
            if occurrence:
                occurrence_dicts.append(occurrence)
        return occurrence_dicts

    def get_occurrences(self):
        return self.occurrences

class Month(Period):
    """
    The month period has functions for retrieving the week periods within this period
    and day periods within the date.
    """
    def __init__(self, events, date=datetime.datetime.now()):
        start, end = self._get_month_range(date)
        super(Month, self).__init__(events, start, end)

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


    def next_month(self):
        return self.end
    
    def prev_month(self):
        return self.start - datetime.timedelta(days=1)

    def _get_month_range(self, month):
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
        start, end = self._get_week_range(date)
        super(Week, self).__init__(events, start, end)

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

class Day(Period):
    def __init__(self, events, date=datetime.date.today()):
        self.events=events
        if isinstance(date, datetime.datetime):
            date = date.date()
        self.start = datetime.datetime.combine(date, datetime.time.min)
        self.end = self.start + datetime.timedelta(days=1)
        self.occurrences = self._get_sorted_occurrences()

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
