import datetime
from django.db.models.query import QuerySet
from django.template.defaultfilters import date
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.dates import WEEKDAYS, WEEKDAYS_ABBR
from schedule.conf.settings import FIRST_DAY_OF_WEEK, SHOW_CANCELLED_OCCURRENCES
from schedule.models import Occurrence
from schedule.utils import OccurrenceReplacer

weekday_names = []
weekday_abbrs = []
if FIRST_DAY_OF_WEEK == 1:
    # The calendar week starts on Monday
    for i in range(7):
        weekday_names.append( WEEKDAYS[i] )
        weekday_abbrs.append( WEEKDAYS_ABBR[i] )
else:
    # The calendar week starts on Sunday, not Monday
    weekday_names.append( WEEKDAYS[6] )
    weekday_abbrs.append( WEEKDAYS_ABBR[6] )
    for i in range(6):
        weekday_names.append( WEEKDAYS[i] )
        weekday_abbrs.append( WEEKDAYS_ABBR[i] )


class Period(object):
    '''
    This class represents a period of time. It can return a set of occurrences
    based on its events, and its time period (start and end).
    '''
    def __init__(self, events, start, end, parent_persisted_occurrences = None,
        occurrence_pool=None):
        self.start = start
        self.end = end
        self.events = events
        self.occurrence_pool = occurrence_pool
        if parent_persisted_occurrences is not None:
            self._persisted_occurrences = parent_persisted_occurrences

    def __eq__(self, period):
        return self.start==period.start and self.end==period.end and self.events==period.events

    def __ne__(self, period):
        return self.start!=period.start or self.end!=period.end or self.events!=period.events

    def _get_sorted_occurrences(self):
        occurrences = []
        if hasattr(self, "occurrence_pool") and self.occurrence_pool is not None:
            for occurrence in self.occurrence_pool:
                if occurrence.start <= self.end and occurrence.end >= self.start:
                    occurrences.append(occurrence)
            return occurrences
        for event in self.events:
            event_occurrences = event.get_occurrences(self.start, self.end)
            occurrences += event_occurrences
        return sorted(occurrences)

    def cached_get_sorted_occurrences(self):
        if hasattr(self, '_occurrences'):
            return self._occurrences
        occs = self._get_sorted_occurrences()
        self._occurrences = occs
        return occs
    occurrences = property(cached_get_sorted_occurrences)

    def get_persisted_occurrences(self):
        if hasattr(self, '_persisted_occurrenes'):
            return self._persisted_occurrences
        else:
            self._persisted_occurrences = Occurrence.objects.filter(event__in = self.events)
            return self._persisted_occurrences

    def classify_occurrence(self, occurrence):
        if occurrence.cancelled and not SHOW_CANCELLED_OCCURRENCES:
            return
        if occurrence.start > self.end or occurrence.end < self.start:
            return None
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

    def has_occurrences(self):
        for occurrence in self.occurrences:
            occurrence = self.classify_occurrence(occurrence)
            if occurrence:
                return True
        return False

    def get_time_slot(self, start, end ):
        if start >= self.start and end <= self.end:
            return Period( self.events, start, end )
        return None

    def create_sub_period(self, cls, start=None):
        start = start or self.start
        return cls(self.events, start, self.get_persisted_occurrences(), self.occurrences)

    def get_periods(self, cls):
        period = self.create_sub_period(cls)
        while period.start < self.end:
            yield self.create_sub_period(cls, period.start)
            period = period.next()


class Year(Period):
    def __init__(self, events, date=None, parent_persisted_occurrences=None):
        if date is None:
            date = datetime.datetime.now()
        start, end = self._get_year_range(date)
        super(Year, self).__init__(events, start, end, parent_persisted_occurrences)

    def get_months(self):
        return self.get_periods(Month)

    def next_year(self):
        return Year(self.events, self.end)
    next = next_year

    def prev_year(self):
        start = datetime.datetime(self.start.year-1, self.start.month, self.start.day)
        return Year(self.events, start)
    prev = prev_year

    def _get_year_range(self, year):
        start = datetime.datetime(year.year, datetime.datetime.min.month,
            datetime.datetime.min.day)
        end = datetime.datetime(year.year+1, datetime.datetime.min.month,
            datetime.datetime.min.day)
        return start, end

    def __unicode__(self):
        return self.start.strftime('%Y')



class Month(Period):
    """
    The month period has functions for retrieving the week periods within this period
    and day periods within the date.
    """
    def __init__(self, events, date=None, parent_persisted_occurrences=None,
        occurrence_pool=None):
        if date is None:
            date = datetime.datetime.now()
        start, end = self._get_month_range(date)
        super(Month, self).__init__(events, start, end,
            parent_persisted_occurrences, occurrence_pool)

    def get_weeks(self):
        return self.get_periods(Week)
        date = self.star

    def get_days(self):
        return self.get_periods(Day)

    def get_day(self, daynumber ):
        date = self.start
        if daynumber > 1:
            date += datetime.timedelta(days=daynumber-1)
        return self.create_sub_period(Day, date)

    def next_month(self):
        return Month(self.events, self.end)
    next = next_month

    def prev_month(self):
        start = (self.start - datetime.timedelta(days=1)).replace(day=1)
        return Month(self.events, start)
    prev = prev_month

    def current_year(self):
        return Year(self.events, self.start)

    def prev_year(self):
        start = datetime.datetime.min.replace(year=self.start.year-1)
        return Year(self.events, start)

    def next_year(self):
        start = datetime.datetime.min.replace(year=self.start.year+1)
        return Year(self.events, start)

    def _get_month_range(self, month):
        year = month.year
        month = month.month
        start = datetime.datetime.min.replace(year=year, month=month)
        if month == 12:
            end = start.replace(month=1, year=year+1)
        else:
            end = start.replace(month=month+1)
        return start, end

    def __unicode__(self):
        return self.name()

    def name(self):
        return self.start.strftime('%B')

    def year(self):
        return self.start.strftime('%Y')


class Week(Period):
    """
    The Week period that has functions for retrieving Day periods within it
    """
    def __init__(self, events, date=None, parent_persisted_occurrences=None,
        occurrence_pool=None):
        if date is None:
            date = datetime.datetime.now()
        start, end = self._get_week_range(date)
        super(Week, self).__init__(events, start, end,
            parent_persisted_occurrences, occurrence_pool)

    def prev_week(self):
        return Week(self.events, self.start - datetime.timedelta(days=7))
    prev = prev_week

    def next_week(self):
        return Week(self.events, self.end)
    next = next_week

    def current_month(self):
        return Month(self.events, self.start)

    def current_year(self):
        return Year(self.events, self.start)

    def get_days(self):
        return self.get_periods(Day)

    def _get_week_range(self, week):
        if isinstance(week, datetime.datetime):
            week = week.date()
        # Adjust the start datetime to midnight of the week datetime
        start = datetime.datetime.combine(week, datetime.time.min)
        # Adjust the start datetime to Monday or Sunday of the current week
        sub_days = 0
        if FIRST_DAY_OF_WEEK == 1:
            # The week begins on Monday
            sub_days = start.isoweekday() - 1
        else:
            # The week begins on Sunday
            sub_days = start.isoweekday()
            if sub_days == 7:
                sub_days = 0
        if sub_days > 0:
            start = start - datetime.timedelta(days=sub_days)
        end = start + datetime.timedelta(days=7)
        return start, end

    def __unicode__(self):
        date_format = u'l, %s' % ugettext("DATE_FORMAT")
        return ugettext('Week: %(start)s-%(end)s') % {
            'start': date(self.start, date_format),
            'end': date(self.end, date_format),
        }


class Day(Period):
    def __init__(self, events, date=None, parent_persisted_occurrences=None,
        occurrence_pool=None):
        if date is None:
            date = datetime.datetime.now()
        start, end = self._get_day_range(date)
        super(Day, self).__init__(events, start, end,
            parent_persisted_occurrences, occurrence_pool)

    def _get_day_range(self, date):
        if isinstance(date, datetime.datetime):
            date = date.date()
        start = datetime.datetime.combine(date, datetime.time.min)
        end = start + datetime.timedelta(days=1)
        return start, end

    def __unicode__(self):
        date_format = u'l, %s' % ugettext("DATE_FORMAT")
        return ugettext('Day: %(start)s-%(end)s') % {
            'start': date(self.start, date_format),
            'end': date(self.end, date_format),
        }

    def prev_day(self):
        return Day(self.events, self.start - datetime.timedelta(days=1))
    prev = prev_day

    def next_day(self):
        return Day(self.events, self.end)
    next = next_day

    def current_year(self):
        return Year(self.events, self.start)

    def current_month(self):
        return Month(self.events, self.start)

    def current_week(self):
        return Week(self.events, self.start)

