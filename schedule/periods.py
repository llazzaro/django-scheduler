import calendar as standardlib_calendar
import datetime

import pytz
from django.conf import settings
from django.db.models.query import prefetch_related_objects
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.utils.dates import WEEKDAYS, WEEKDAYS_ABBR
from django.utils.translation import gettext

from schedule.models import Occurrence
from schedule.settings import SHOW_CANCELLED_OCCURRENCES

weekday_names = []
weekday_abbrs = []

if settings.FIRST_DAY_OF_WEEK == 1:
    # The calendar week starts on Monday
    for i in range(7):
        weekday_names.append(WEEKDAYS[i])
        weekday_abbrs.append(WEEKDAYS_ABBR[i])
else:
    # The calendar week starts on Sunday, not Monday
    weekday_names.append(WEEKDAYS[6])
    weekday_abbrs.append(WEEKDAYS_ABBR[6])
    for i in range(6):
        weekday_names.append(WEEKDAYS[i])
        weekday_abbrs.append(WEEKDAYS_ABBR[i])


class Period:
    """
    This class represents a period of time. It can return a set of occurrences
    based on its events, and its time period (start and end).
    """

    def __init__(
        self,
        events,
        start,
        end,
        parent_persisted_occurrences=None,
        occurrence_pool=None,
        tzinfo=pytz.utc,
        sorting_options=None,
    ):

        self.utc_start = self._normalize_timezone_to_utc(start, tzinfo)

        self.utc_end = self._normalize_timezone_to_utc(end, tzinfo)

        self.events = events
        self.tzinfo = self._get_tzinfo(tzinfo)
        self.occurrence_pool = occurrence_pool
        if parent_persisted_occurrences is not None:
            self._persisted_occurrences = parent_persisted_occurrences
        self.sorting_options = sorting_options or {}

    def _normalize_timezone_to_utc(self, point_in_time, tzinfo):
        if point_in_time.tzinfo is not None:
            return point_in_time.astimezone(pytz.utc)
        if tzinfo is not None:
            return pytz.timezone(str(tzinfo)).localize(point_in_time)
        if settings.USE_TZ:
            return pytz.utc.localize(point_in_time)
        else:
            if timezone.is_aware(point_in_time):
                return timezone.make_naive(point_in_time, pytz.utc)
            else:
                return point_in_time

    def __eq__(self, period):
        return (
            self.utc_start == period.utc_start
            and self.utc_end == period.utc_end
            and self.events == period.events
        )

    def _get_tzinfo(self, tzinfo):
        return tzinfo if settings.USE_TZ else None

    def _get_sorted_occurrences(self):
        occurrences = []
        if hasattr(self, "occurrence_pool") and self.occurrence_pool is not None:
            for occurrence in self.occurrence_pool:
                if (
                    occurrence.start <= self.utc_end
                    and occurrence.end >= self.utc_start
                ):
                    occurrences.append(occurrence)
        else:
            prefetch_related_objects(self.events, "occurrence_set")
            for event in self.events:
                event_occurrences = event.get_occurrences(
                    self.start, self.end, clear_prefetch=False
                )
                occurrences += event_occurrences
        return sorted(occurrences, **self.sorting_options)

    def cached_get_sorted_occurrences(self):
        if hasattr(self, "_occurrences"):
            return self._occurrences
        occs = self._get_sorted_occurrences()
        self._occurrences = occs
        return occs

    occurrences = property(cached_get_sorted_occurrences)

    def get_persisted_occurrences(self):
        if hasattr(self, "_persisted_occurrences"):
            return self._persisted_occurrences
        else:
            self._persisted_occurrences = Occurrence.objects.filter(
                event__in=self.events
            )
            return self._persisted_occurrences

    def classify_occurrence(self, occurrence):
        if occurrence.cancelled and not SHOW_CANCELLED_OCCURRENCES:
            return
        if occurrence.start > self.end or occurrence.end < self.start:
            return None
        started = False
        ended = False
        if self.utc_start <= occurrence.start < self.utc_end:
            started = True
        if self.utc_start <= occurrence.end < self.utc_end:
            ended = True
        if started and ended:
            return {"occurrence": occurrence, "class": 1}
        elif started:
            return {"occurrence": occurrence, "class": 0}
        elif ended:
            return {"occurrence": occurrence, "class": 3}
        # it existed during this period but it didn't begin or end within it
        # so it must have just continued
        return {"occurrence": occurrence, "class": 2}

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
        return any(self.classify_occurrence(o) for o in self.occurrences)

    def get_time_slot(self, start, end):
        if start >= self.start and end <= self.end:
            return Period(self.events, start, end, tzinfo=self.tzinfo)
        return Period([], start, end, tzinfo=self.tzinfo)

    def create_sub_period(self, cls, start=None, tzinfo=None):
        if tzinfo is None:
            tzinfo = self.tzinfo
        start = start or self.start
        return cls(
            self.events,
            start,
            self.get_persisted_occurrences(),
            self.occurrences,
            tzinfo,
        )

    def get_periods(self, cls, tzinfo=None):
        if tzinfo is None:
            tzinfo = self.tzinfo
        period = self.create_sub_period(cls)
        while period.start < self.end:
            yield self.create_sub_period(cls, period.start, tzinfo)
            period = next(period)

    @property
    def start(self):
        if self.tzinfo is not None:
            return self.utc_start.astimezone(self.tzinfo)
        return self.utc_start.replace(tzinfo=None)

    @property
    def end(self):
        if self.tzinfo is not None:
            return self.utc_end.astimezone(self.tzinfo)
        return self.utc_end.replace(tzinfo=None)


class Year(Period):
    def __init__(
        self, events, date=None, parent_persisted_occurrences=None, tzinfo=pytz.utc
    ):
        self.tzinfo = self._get_tzinfo(tzinfo)
        if date is None:
            date = timezone.now()
        start, end = self._get_year_range(date)
        super().__init__(
            events, start, end, parent_persisted_occurrences, tzinfo=tzinfo
        )

    def get_months(self):
        return self.get_periods(Month)

    def next_year(self):
        return Year(self.events, self.end, tzinfo=self.tzinfo)

    next = __next__ = next_year

    def prev_year(self):
        start = datetime.datetime(self.start.year - 1, self.start.month, self.start.day)
        return Year(self.events, start, tzinfo=self.tzinfo)

    prev = prev_year

    def _get_year_range(self, year):
        # If tzinfo is not none get the local start of the year and convert it to utc.
        naive_start = datetime.datetime(
            year.year, datetime.datetime.min.month, datetime.datetime.min.day
        )
        naive_end = datetime.datetime(
            year.year + 1, datetime.datetime.min.month, datetime.datetime.min.day
        )

        start = naive_start
        end = naive_end
        if self.tzinfo is not None:
            local_start = pytz.timezone(str(self.tzinfo)).localize(naive_start)
            local_end = pytz.timezone(str(self.tzinfo)).localize(naive_end)
            start = local_start.astimezone(pytz.utc)
            end = local_end.astimezone(pytz.utc)

        return start, end

    def __str__(self):
        return self.start.year


class Month(Period):
    """
    The month period has functions for retrieving the week periods within this period
    and day periods within the date.
    """

    def __init__(
        self,
        events,
        date=None,
        parent_persisted_occurrences=None,
        occurrence_pool=None,
        tzinfo=pytz.utc,
    ):
        self.tzinfo = self._get_tzinfo(tzinfo)
        if date is None:
            date = timezone.now()
        start, end = self._get_month_range(date)
        super().__init__(
            events,
            start,
            end,
            parent_persisted_occurrences,
            occurrence_pool,
            tzinfo=tzinfo,
        )

    def get_weeks(self):
        return self.get_periods(Week)

    def get_days(self):
        return self.get_periods(Day)

    def get_day(self, daynumber):
        date = self.start
        if daynumber > 1:
            date += datetime.timedelta(days=daynumber - 1)
        return self.create_sub_period(Day, date)

    def next_month(self):
        return Month(self.events, self.end, tzinfo=self.tzinfo)

    next = __next__ = next_month

    def prev_month(self):
        start = (self.start - datetime.timedelta(days=1)).replace(
            day=1, tzinfo=self.tzinfo
        )
        return Month(self.events, start, tzinfo=self.tzinfo)

    prev = prev_month

    def current_year(self):
        return Year(self.events, self.start, tzinfo=self.tzinfo)

    def prev_year(self):
        start = datetime.datetime.min.replace(
            year=self.start.year - 1, tzinfo=self.tzinfo
        )
        return Year(self.events, start, tzinfo=self.tzinfo)

    def next_year(self):
        start = datetime.datetime.min.replace(
            year=self.start.year + 1, tzinfo=self.tzinfo
        )
        return Year(self.events, start, tzinfo=self.tzinfo)

    def _get_month_range(self, month):
        year = month.year
        month = month.month
        # If tzinfo is not none get the local start of the month and convert it to utc.
        naive_start = datetime.datetime.min.replace(year=year, month=month)
        if month == 12:
            naive_end = datetime.datetime.min.replace(month=1, year=year + 1, day=1)
        else:
            naive_end = datetime.datetime.min.replace(month=month + 1, year=year, day=1)

        start = naive_start
        end = naive_end
        if self.tzinfo is not None:
            local_start = pytz.timezone(str(self.tzinfo)).localize(naive_start)
            local_end = pytz.timezone(str(self.tzinfo)).localize(naive_end)
            start = local_start.astimezone(pytz.utc)
            end = local_end.astimezone(pytz.utc)

        return start, end

    def __str__(self):
        return self.name()

    def name(self):
        return standardlib_calendar.month_name[self.start.month]

    def year(self):
        return self.start.year


class Week(Period):
    """
    The Week period that has functions for retrieving Day periods within it
    """

    def __init__(
        self,
        events,
        date=None,
        parent_persisted_occurrences=None,
        occurrence_pool=None,
        tzinfo=pytz.utc,
    ):
        self.tzinfo = self._get_tzinfo(tzinfo)
        if date is None:
            date = timezone.now()
        start, end = self._get_week_range(date)
        super().__init__(
            events,
            start,
            end,
            parent_persisted_occurrences,
            occurrence_pool,
            tzinfo=tzinfo,
        )

    def prev_week(self):
        return Week(
            self.events, self.start - datetime.timedelta(days=7), tzinfo=self.tzinfo
        )

    prev = prev_week

    def next_week(self):
        return Week(self.events, self.end, tzinfo=self.tzinfo)

    next = __next__ = next_week

    def current_month(self):
        return Month(self.events, self.start, tzinfo=self.tzinfo)

    def current_year(self):
        return Year(self.events, self.start, tzinfo=self.tzinfo)

    def get_days(self):
        return self.get_periods(Day)

    def _get_week_range(self, week):
        if isinstance(week, datetime.datetime):
            week = week.date()
        # Adjust the start datetime to midnight of the week datetime
        naive_start = datetime.datetime.combine(week, datetime.time.min)
        # Adjust the start datetime to Monday or Sunday of the current week
        if settings.FIRST_DAY_OF_WEEK == 1:
            # The week begins on Monday
            sub_days = naive_start.isoweekday() - 1
        else:
            # The week begins on Sunday
            sub_days = naive_start.isoweekday()
            if sub_days == 7:
                sub_days = 0
        if sub_days > 0:
            naive_start = naive_start - datetime.timedelta(days=sub_days)
        naive_end = naive_start + datetime.timedelta(days=7)

        if self.tzinfo is not None:
            local_start = pytz.timezone(str(self.tzinfo)).localize(naive_start)
            local_end = pytz.timezone(str(self.tzinfo)).localize(naive_end)
            start = local_start.astimezone(pytz.utc)
            end = local_end.astimezone(pytz.utc)
        else:
            start = naive_start
            end = naive_end

        return start, end

    def __str__(self):
        date_format = "l, %s" % settings.DATE_FORMAT
        return gettext("Week: %(start)s-%(end)s") % {
            "start": date_filter(self.start, date_format),
            "end": date_filter(self.end, date_format),
        }


class Day(Period):
    def __init__(
        self,
        events,
        date=None,
        parent_persisted_occurrences=None,
        occurrence_pool=None,
        tzinfo=pytz.utc,
    ):
        self.tzinfo = self._get_tzinfo(tzinfo)
        if date is None:
            date = timezone.now()
        start, end = self._get_day_range(date)
        super().__init__(
            events,
            start,
            end,
            parent_persisted_occurrences,
            occurrence_pool,
            tzinfo=tzinfo,
        )

    def _get_day_range(self, date):

        # localize the date before we typecast to naive dates
        if self.tzinfo is not None and timezone.is_aware(date):
            date = date.astimezone(self.tzinfo)

        if isinstance(date, datetime.datetime):
            date = date.date()

        naive_start = datetime.datetime.combine(date, datetime.time.min)
        naive_end = datetime.datetime.combine(
            date + datetime.timedelta(days=1), datetime.time.min
        )
        if self.tzinfo is not None:
            local_start = pytz.timezone(str(self.tzinfo)).localize(naive_start)
            local_end = pytz.timezone(str(self.tzinfo)).localize(naive_end)
            start = local_start.astimezone(pytz.utc)
            end = local_end.astimezone(pytz.utc)
        else:
            start = naive_start
            end = naive_end

        return start, end

    def __str__(self):
        date_format = "l, %s" % settings.DATE_FORMAT
        return gettext("Day: %(start)s-%(end)s") % {
            "start": date_filter(self.start, date_format),
            "end": date_filter(self.end, date_format),
        }

    def prev_day(self):
        return Day(
            self.events, self.start - datetime.timedelta(days=1), tzinfo=self.tzinfo
        )

    prev = prev_day

    def next_day(self):
        return Day(self.events, self.end, tzinfo=self.tzinfo)

    next = __next__ = next_day

    def current_year(self):
        return Year(self.events, self.start, tzinfo=self.tzinfo)

    def current_month(self):
        return Month(self.events, self.start, tzinfo=self.tzinfo)

    def current_week(self):
        return Week(self.events, self.start, tzinfo=self.tzinfo)
