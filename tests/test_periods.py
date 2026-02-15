import datetime

import pytz
from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext, override_settings

from schedule.models import Calendar, Event, Rule
from schedule.models.events import Occurrence
from schedule.periods import Day, Month, Period, Week, Year


class TestPeriod(TestCase):
    def setUp(self):
        rule = Rule.objects.create(frequency="WEEKLY")
        cal = Calendar.objects.create(name="MyCal")
        Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )
        self.period = Period(
            events=Event.objects.all(),
            start=datetime.datetime(2008, 1, 4, 7, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 21, 7, 0, tzinfo=pytz.utc),
        )

    def test_get_occurrences(self):
        occurrence_list = self.period.occurrences
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrence_list],
            [
                "2008-01-05 08:00:00+00:00 to 2008-01-05 09:00:00+00:00",
                "2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00",
                "2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00",
            ],
        )

    def test_nplus_one_queries_event_period(self):
        """Reproduces bug 420 occurences without title or desc will generate additional queries
        to retrieve the event model
        """
        rule = Rule.objects.create(frequency="WEEKLY")
        cal = Calendar.objects.get(name="MyCal")

        event = Event.objects.create(
            title="TEST",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2023, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )
        for _ in range(0, 21):
            # lets set occ without title and desc to use the event.title or event.desc
            Occurrence.objects.create(
                event=event,
                start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
                end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
                original_start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
                original_end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            )
        period = Period(
            events=[event],
            start=datetime.datetime(2008, 1, 4, 7, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2023, 1, 21, 7, 0, tzinfo=pytz.utc),
        )
        with CaptureQueriesContext(connection) as ctx:
            for occurrence in period.get_occurrences():
                pass

        executed_queries = len(ctx.captured_queries)
        assert executed_queries == 1, len(ctx.captured_queries)

    def test_get_occurrences_with_sorting_options(self):
        period = Period(
            events=Event.objects.all(),
            start=datetime.datetime(2008, 1, 4, 7, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 21, 7, 0, tzinfo=pytz.utc),
            sorting_options={"reverse": True},
        )
        occurrence_list = period.occurrences
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrence_list],
            [
                "2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00",
                "2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00",
                "2008-01-05 08:00:00+00:00 to 2008-01-05 09:00:00+00:00",
            ],
        )

    def test_get_occurrence_partials(self):
        occurrence_dicts = self.period.get_occurrence_partials()
        self.assertEqual(
            [
                (
                    occ_dict["class"],
                    occ_dict["occurrence"].start,
                    occ_dict["occurrence"].end,
                )
                for occ_dict in occurrence_dicts
            ],
            [
                (
                    1,
                    datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                ),
                (
                    1,
                    datetime.datetime(2008, 1, 12, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 12, 9, 0, tzinfo=pytz.utc),
                ),
                (
                    1,
                    datetime.datetime(2008, 1, 19, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 19, 9, 0, tzinfo=pytz.utc),
                ),
            ],
        )

    def test_has_occurrence(self):
        self.assertTrue(self.period.has_occurrences())
        slot = self.period.get_time_slot(
            datetime.datetime(2008, 1, 4, 7, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 4, 7, 12, tzinfo=pytz.utc),
        )
        self.assertFalse(slot.has_occurrences())


class TestYear(TestCase):
    def setUp(self):
        self.year = Year(events=[], date=datetime.datetime(2008, 4, 1, tzinfo=pytz.utc))

    def test_get_months(self):
        months = self.year.get_months()
        self.assertEqual(
            [month.start for month in months],
            [datetime.datetime(2008, i, 1, tzinfo=pytz.utc) for i in range(1, 13)],
        )


class TestMonth(TestCase):
    def setUp(self):
        rule = Rule.objects.create(frequency="WEEKLY")
        cal = Calendar.objects.create(name="MyCal")
        Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )
        self.month = Month(
            events=Event.objects.all(),
            date=datetime.datetime(2008, 2, 7, 9, 0, tzinfo=pytz.utc),
        )

    def test_get_weeks(self):
        weeks = self.month.get_weeks()
        actuals = [(week.start, week.end) for week in weeks]

        if settings.FIRST_DAY_OF_WEEK == 0:
            expecteds = [
                (
                    datetime.datetime(2008, 1, 27, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 3, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 3, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 10, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 10, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 17, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 17, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 24, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 24, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 3, 2, 0, 0, tzinfo=pytz.utc),
                ),
            ]
        else:
            expecteds = [
                (
                    datetime.datetime(2008, 1, 28, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 4, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 4, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 11, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 11, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 18, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 18, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 25, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    datetime.datetime(2008, 2, 25, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 3, 3, 0, 0, tzinfo=pytz.utc),
                ),
            ]

        for actual, expected in zip(actuals, expecteds):
            self.assertEqual(actual, expected)

    def test_get_days(self):
        weeks = self.month.get_weeks()
        week = list(weeks)[0]
        days = week.get_days()
        actuals = [(len(day.occurrences), day.start, day.end) for day in days]

        if settings.FIRST_DAY_OF_WEEK == 0:
            expecteds = [
                (
                    0,
                    datetime.datetime(2008, 1, 27, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 28, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 28, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 29, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 29, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 30, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 30, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 31, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 31, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 1, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 2, 1, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 2, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    1,
                    datetime.datetime(2008, 2, 2, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 3, 0, 0, tzinfo=pytz.utc),
                ),
            ]

        else:
            expecteds = [
                (
                    0,
                    datetime.datetime(2008, 1, 28, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 29, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 29, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 30, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 30, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 31, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 1, 31, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 1, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 2, 1, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 2, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    1,
                    datetime.datetime(2008, 2, 2, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 3, 0, 0, tzinfo=pytz.utc),
                ),
                (
                    0,
                    datetime.datetime(2008, 2, 3, 0, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 2, 4, 0, 0, tzinfo=pytz.utc),
                ),
            ]

        for actual, expected in zip(actuals, expecteds):
            self.assertEqual(actual, expected)

    def test_month_convenience_functions(self):
        self.assertEqual(
            self.month.prev_month().start,
            datetime.datetime(2008, 1, 1, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            self.month.next_month().start,
            datetime.datetime(2008, 3, 1, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            self.month.current_year().start,
            datetime.datetime(2008, 1, 1, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            self.month.prev_year().start,
            datetime.datetime(2007, 1, 1, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            self.month.next_year().start,
            datetime.datetime(2009, 1, 1, 0, 0, tzinfo=pytz.utc),
        )


class TestDay(TestCase):
    def setUp(self):
        self.day = Day(
            events=Event.objects.all(),
            date=datetime.datetime(2008, 2, 7, 9, 0, tzinfo=pytz.utc),
        )

    def test_day_setup(self):
        self.assertEqual(
            self.day.start, datetime.datetime(2008, 2, 7, 0, 0, tzinfo=pytz.utc)
        )
        self.assertEqual(
            self.day.end, datetime.datetime(2008, 2, 8, 0, 0, tzinfo=pytz.utc)
        )

    def test_day_convenience_functions(self):
        self.assertEqual(
            self.day.prev_day().start,
            datetime.datetime(2008, 2, 6, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            self.day.next_day().start,
            datetime.datetime(2008, 2, 8, 0, 0, tzinfo=pytz.utc),
        )

    def test_time_slot(self):
        slot_start = datetime.datetime(2008, 2, 7, 13, 30, tzinfo=pytz.utc)
        slot_end = datetime.datetime(2008, 2, 7, 15, 0, tzinfo=pytz.utc)
        period = self.day.get_time_slot(slot_start, slot_end)
        self.assertEqual(period.start, slot_start)
        self.assertEqual(period.end, slot_end)

    def test_time_slot_with_dst(self):
        tzinfo = pytz.timezone("America/Vancouver")
        slot_start = datetime.datetime(2016, 3, 13, 0, 0, tzinfo=tzinfo)
        slot_end = datetime.datetime(2016, 3, 14, 0, 0, tzinfo=tzinfo)
        period = self.day.get_time_slot(slot_start, slot_end)
        self.assertEqual(period.start, slot_start)
        self.assertEqual(period.end, slot_end)

    def test_get_day_range(self):
        # This test exercises the case where a Day object is initiatized with
        # no date, which causes the Day constructor to call timezone.now(),
        # which always uses UTC.  This can cause a problem if the desired TZ
        # is not UTC, because the _get_day_range method typecasts the
        # tz-aware datetime to a naive datetime.

        # To simulate this case, we will create a NY tz date, localize that
        # date to UTC, then create a Day object with the UTC date and NY TZ

        NY = pytz.timezone("America/New_York")
        user_wall_time = datetime.datetime(2015, 11, 4, 21, 30, tzinfo=NY)
        timezone_now = user_wall_time.astimezone(pytz.utc)

        test_day = Day(events=Event.objects.all(), date=timezone_now, tzinfo=NY)

        expected_start = datetime.datetime(2015, 11, 4, 5, 00, tzinfo=pytz.utc)
        expected_end = datetime.datetime(2015, 11, 5, 5, 00, tzinfo=pytz.utc)

        self.assertEqual(test_day.start, expected_start)
        self.assertEqual(test_day.end, expected_end)


class TestOccurrencePool(TestCase):
    def setUp(self):
        rule = Rule.objects.create(frequency="WEEKLY")
        cal = Calendar.objects.create(name="MyCal")
        self.recurring_event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )

    def testPeriodFromPool(self):
        """
        Test that period initiated with occurrence_pool returns the same occurrences as "straigh" period
        in a corner case whereby a period's start date is equal to the occurrence's end date
        """
        start = datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc)
        end = datetime.datetime(2008, 1, 5, 10, 0, tzinfo=pytz.utc)
        parent_period = Period(Event.objects.all(), start, end)
        period = Period(
            parent_period.events,
            start,
            end,
            parent_period.get_persisted_occurrences(),
            parent_period.occurrences,
        )
        self.assertEqual(parent_period.occurrences, period.occurrences)


class TestOccurrencesInTimezone(TestCase):
    def setUp(self):
        self.MVD = pytz.timezone("America/Montevideo")
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(
            frequency="DAILY", params="byweekday:SA", name="Saturdays"
        )
        Event.objects.create(
            title="Every Saturday Event",
            start=self.MVD.localize(datetime.datetime(2017, 1, 7, 22, 0)),
            end=self.MVD.localize(datetime.datetime(2017, 1, 7, 23, 0)),
            end_recurring_period=self.MVD.localize(datetime.datetime(2017, 2, 1)),
            rule=rule,
            calendar=cal,
        )

    @override_settings(TIME_ZONE="America/Montevideo")
    def test_occurrences_with_TZ(self):
        start = self.MVD.localize(datetime.datetime(2017, 1, 13))
        end = self.MVD.localize(datetime.datetime(2017, 1, 23))

        period = Period(Event.objects.all(), start, end, tzinfo=self.MVD)
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in period.occurrences],
            [
                "2017-01-14 22:00:00-03:00 to 2017-01-14 23:00:00-03:00",
                "2017-01-21 22:00:00-03:00 to 2017-01-21 23:00:00-03:00",
            ],
        )

    @override_settings(TIME_ZONE="America/Montevideo")
    def test_occurrences_sub_period_with_TZ(self):
        start = self.MVD.localize(datetime.datetime(2017, 1, 13))
        end = self.MVD.localize(datetime.datetime(2017, 1, 23))

        period = Period(Event.objects.all(), start, end, tzinfo=self.MVD)

        sub_start = self.MVD.localize(datetime.datetime(2017, 1, 13))
        sub_end = self.MVD.localize(datetime.datetime(2017, 1, 15))
        sub_period = period.get_time_slot(sub_start, sub_end)
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in sub_period.occurrences],
            ["2017-01-14 22:00:00-03:00 to 2017-01-14 23:00:00-03:00"],
        )


class TestWeeklyOccurrences(TestCase):
    def setUp(self):
        self.MVD = pytz.timezone("America/Montevideo")  # UTC-3
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY", name="daily")
        Event.objects.create(
            title="Test event",
            start=self.MVD.localize(datetime.datetime(2017, 1, 13, 15, 0)),
            end=self.MVD.localize(datetime.datetime(2017, 1, 14, 15, 0)),
            end_recurring_period=self.MVD.localize(datetime.datetime(2017, 1, 20)),
            rule=rule,
            calendar=cal,
        )

    def test_occurrences_inside_recurrence_period(self):
        start = self.MVD.localize(datetime.datetime(2017, 1, 13))

        period = Week(Event.objects.all(), start, tzinfo=self.MVD)

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in period.occurrences],
            [
                "2017-01-13 15:00:00-03:00 to 2017-01-14 15:00:00-03:00",
                "2017-01-14 15:00:00-03:00 to 2017-01-15 15:00:00-03:00",
            ],
        )

    def test_occurrences_outside_recurrence_period(self):
        start = self.MVD.localize(datetime.datetime(2017, 1, 23))

        period = Week(Event.objects.all(), start, tzinfo=self.MVD)

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in period.occurrences], []
        )

    def test_occurrences_no_end(self):
        event = Event.objects.filter(title="Test event").get()
        event.end_recurring_period = None
        start = self.MVD.localize(datetime.datetime(2018, 1, 13))

        period = Week([event], start, tzinfo=self.MVD)

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in period.occurrences],
            [
                "2018-01-06 15:00:00-03:00 to 2018-01-07 15:00:00-03:00",
                "2018-01-07 15:00:00-03:00 to 2018-01-08 15:00:00-03:00",
                "2018-01-08 15:00:00-03:00 to 2018-01-09 15:00:00-03:00",
                "2018-01-09 15:00:00-03:00 to 2018-01-10 15:00:00-03:00",
                "2018-01-10 15:00:00-03:00 to 2018-01-11 15:00:00-03:00",
                "2018-01-11 15:00:00-03:00 to 2018-01-12 15:00:00-03:00",
                "2018-01-12 15:00:00-03:00 to 2018-01-13 15:00:00-03:00",
                "2018-01-13 15:00:00-03:00 to 2018-01-14 15:00:00-03:00",
            ],
        )

    def test_occurrences_end_in_diff_tz(self):
        event = Event.objects.filter(title="Test event").get()
        AMSTERDAM = pytz.timezone("Europe/Amsterdam")
        # 2017-01-14 00:00 CET = 2017-01-13 21:00 UYT
        event.end_recurring_period = AMSTERDAM.localize(
            datetime.datetime(2017, 1, 14, 0, 0)
        )
        start = self.MVD.localize(datetime.datetime(2017, 1, 13))

        period = Week([event], start, tzinfo=self.MVD)

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in period.occurrences],
            ["2017-01-13 15:00:00-03:00 to 2017-01-14 15:00:00-03:00"],
        )


class TestAwareDay(TestCase):
    def setUp(self):
        self.timezone = pytz.timezone("Europe/Amsterdam")

        start = self.timezone.localize(datetime.datetime(2008, 2, 7, 0, 20))
        end = self.timezone.localize(datetime.datetime(2008, 2, 7, 0, 21))
        self.event = Event.objects.create(
            title="One minute long event on january seventh 2008 at 00:20 in Amsterdam.",
            start=start,
            end=end,
            calendar=Calendar.objects.create(name="MyCal"),
        )

        self.day = Day(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2008, 2, 7, 9, 0)),
            tzinfo=self.timezone,
        )

    def test_day_range(self):
        start = datetime.datetime(2008, 2, 6, 23, 0, tzinfo=pytz.utc)
        end = datetime.datetime(2008, 2, 7, 23, 0, tzinfo=pytz.utc)

        self.assertEqual(start, self.day.start)
        self.assertEqual(end, self.day.end)

    def test_occurrence(self):
        self.assertEqual(self.event in [o.event for o in self.day.occurrences], True)


class TestTzInfoPersistence(TestCase):
    def setUp(self):
        self.timezone = pytz.timezone("Europe/Amsterdam")
        self.day = Day(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

        self.week = Week(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

        self.month = Month(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

        self.year = Year(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

    def test_persistence(self):
        self.assertEqual(self.day.tzinfo, self.timezone)
        self.assertEqual(self.week.tzinfo, self.timezone)
        self.assertEqual(self.month.tzinfo, self.timezone)
        self.assertEqual(self.year.tzinfo, self.timezone)


class TestAwareWeek(TestCase):
    def setUp(self):
        self.timezone = pytz.timezone("Europe/Amsterdam")
        self.week = Week(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

    def test_week_range(self):
        start = self.timezone.localize(datetime.datetime(2013, 12, 15, 0, 0))
        end = self.timezone.localize(datetime.datetime(2013, 12, 22, 0, 0))

        self.assertEqual(self.week.tzinfo, self.timezone)
        self.assertEqual(start, self.week.start)
        self.assertEqual(end, self.week.end)


class TestAwareMonth(TestCase):
    def setUp(self):
        self.timezone = pytz.timezone("Europe/Amsterdam")
        self.month = Month(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 11, 17, 9, 0)),
            tzinfo=self.timezone,
        )

    def test_month_range(self):
        start = self.timezone.localize(datetime.datetime(2013, 11, 1, 0, 0))
        end = self.timezone.localize(datetime.datetime(2013, 12, 1, 0, 0))

        self.assertEqual(self.month.tzinfo, self.timezone)
        self.assertEqual(start, self.month.start)
        self.assertEqual(end, self.month.end)


class TestAwareYear(TestCase):
    def setUp(self):
        self.timezone = pytz.timezone("Europe/Amsterdam")
        self.year = Year(
            events=Event.objects.all(),
            date=self.timezone.localize(datetime.datetime(2013, 12, 17, 9, 0)),
            tzinfo=self.timezone,
        )

    def test_year_range(self):
        start = self.timezone.localize(datetime.datetime(2013, 1, 1, 0, 0))
        end = self.timezone.localize(datetime.datetime(2014, 1, 1, 0, 0))

        self.assertEqual(self.year.tzinfo, self.timezone)
        self.assertEqual(start, self.year.start)
        self.assertEqual(end, self.year.end)


class TestStrftimeRefactor(TestCase):
    """
    Test for the refactor of strftime
    """

    def test_years_before_1900(self):
        d = datetime.date(year=1899, month=1, day=1)
        m = Month([], d)
        try:
            m.name()
        except ValueError as value_error:
            self.fail(value_error)
