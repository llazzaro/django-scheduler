import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from schedule.models import Calendar, Event, EventRelation, Rule


class TestEvent(TestCase):
    def __create_event(self, title, start, end, cal):
        return Event.objects.create(title=title, start=start, end=end, calendar=cal)

    def __create_recurring_event(self, title, start, end, end_recurring, rule, cal):
        return Event.objects.create(
            title=title,
            start=start,
            end=end,
            end_recurring_period=end_recurring,
            rule=rule,
            calendar=cal,
        )

    def test_edge_case_events(self):
        cal = Calendar.objects.create(name="MyCal")
        event_one = Event.objects.create(
            title="Edge case event test one",
            start=datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            calendar=cal,
        )
        event_two = Event.objects.create(
            title="Edge case event test two",
            start=datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
            calendar=cal,
        )
        occurrences_two = event_two.get_occurrences(
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences(
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(0, len(occurrences_one))

    def test_recurring_event_get_occurrences(self):

        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        occurrences = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc),
        )
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrences],
            [
                "2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00",
                "2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00",
            ],
        )

    def test_event_get_occurrences_after(self):

        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        event_one = self.__create_event(
            "Edge case event test one",
            datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            cal,
        )
        event_two = self.__create_event(
            "Edge case event test two",
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
            cal,
        )
        occurrences_two = event_two.get_occurrences(
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
        )

        self.assertEqual(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences(
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
        )

        self.assertEqual(0, len(occurrences_one))

    def test_recurring_event_get_occurrences_2(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurring event test",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        occurrences = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrences],
            [
                "2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00",
                "2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00",
            ],
        )

    def test_recurring_event_get_occurrences_after(self):

        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")
        recurring_event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        occurrences = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 5, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 6, tzinfo=pytz.utc),
        )
        occurrence = occurrences[0]
        occurrence2 = next(
            recurring_event.occurrences_after(
                datetime.datetime(2008, 1, 5, tzinfo=pytz.utc)
            )
        )
        self.assertEqual(occurrence, occurrence2)

    def test_recurring_event_with_moved_get_occurrences_after(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")
        recurring_event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        occurrence = recurring_event.get_occurrence(
            datetime.datetime(2008, 1, 12, 8, 0, tzinfo=pytz.utc)
        )
        occurrence.move(
            datetime.datetime(2008, 1, 15, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 15, 9, 0, tzinfo=pytz.utc),
        )
        gen = recurring_event.occurrences_after(
            datetime.datetime(2008, 1, 14, 8, 0, tzinfo=pytz.utc)
        )
        occurrence2 = next(gen)
        self.assertEqual(occurrence, occurrence2)

    def test_recurring_event_get_occurrence(self):

        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        occurrence = event.get_occurrence(
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc)
        )
        self.assertEqual(
            occurrence.start, datetime.datetime(2008, 1, 5, 8, tzinfo=pytz.utc)
        )
        occurrence.save()
        occurrence = event.get_occurrence(
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc)
        )
        self.assertTrue(occurrence.pk is not None)

    def test_prevent_type_error_when_comparing_naive_and_aware_dates(self):
        # this only test if the TypeError is raised
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        naive_date = datetime.datetime(2008, 1, 20, 0, 0)
        self.assertIsNone(event.get_occurrence(naive_date))

    @override_settings(USE_TZ=False)
    def test_prevent_type_error_when_comparing_dates_when_tz_off(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2008, 1, 5, 8, 0),
            datetime.datetime(2008, 1, 5, 9, 0),
            datetime.datetime(2008, 5, 5, 0, 0),
            rule,
            cal,
        )
        naive_date = datetime.datetime(2008, 1, 20, 0, 0)
        self.assertIsNone(event.get_occurrence(naive_date))

    @override_settings(USE_TZ=False)
    def test_get_occurrences_when_tz_off(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurring event test",
            datetime.datetime(2008, 1, 5, 8, 0),
            datetime.datetime(2008, 1, 5, 9, 0),
            datetime.datetime(2008, 5, 5, 0, 0),
            rule,
            cal,
        )
        occurrences = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 12, 0, 0),
            end=datetime.datetime(2008, 1, 20, 0, 0),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrences],
            [
                "2008-01-12 08:00:00 to 2008-01-12 09:00:00",
                "2008-01-19 08:00:00 to 2008-01-19 09:00:00",
            ],
        )

    def test_event_get_ocurrence(self):
        cal = Calendar.objects.create(name="MyCal")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            cal,
        )
        occurrence = event.get_occurrence(start)
        self.assertEqual(occurrence.start, start)

    def test_occurrences_after_with_no_params(self):
        cal = Calendar.objects.create(name="MyCal")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            cal,
        )
        occurrences = list(event.occurrences_after())
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].start, start)
        self.assertEqual(occurrences[0].end, start + datetime.timedelta(hours=1))

    def test_occurrences_with_recurrent_event_end_recurring_period_edge_case(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            start + datetime.timedelta(days=10),
            rule,
            cal,
        )
        occurrences = list(event.occurrences_after())
        self.assertEqual(len(occurrences), 11)

    def test_occurrences_with_recurrent_event_end_recurring_period_edge_case_max_loop_lower(
        self,
    ):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            start + datetime.timedelta(days=10),
            rule,
            cal,
        )
        occurrences = list(event.occurrences_after(max_occurrences=4))
        self.assertEqual(len(occurrences), 4)

    def test_occurrences_with_recurrent_event_end_recurring_period_edge_case_max_loop_greater(
        self,
    ):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            start + datetime.timedelta(days=10),
            rule,
            cal,
        )
        occurrences = list(event.occurrences_after(max_occurrences=20))
        self.assertEqual(len(occurrences), 11)

    def test_occurrences_with_recurrent_event_no_end_recurring_period_max_loop(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            start + datetime.timedelta(hours=10),
            rule,
            cal,
        )
        occurrences = list(event.occurrences_after(max_occurrences=1))
        self.assertEqual(len(occurrences), 1)

    def test_get_for_object(self):
        user = User.objects.create_user("john", "lennon@thebeatles.com", "johnpassword")
        event_relations = list(
            Event.objects.get_for_object(user, "owner", inherit=False)
        )
        self.assertEqual(len(event_relations), 0)

        Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        event = self.__create_event(
            "event test",
            datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
            cal,
        )
        events = list(Event.objects.get_for_object(user, "owner", inherit=False))
        self.assertEqual(len(events), 0)
        EventRelation.objects.create_relation(event, user, "owner")

        events = list(Event.objects.get_for_object(user, "owner", inherit=False))
        self.assertEqual(len(events), 1)
        self.assertEqual(event, events[0])

    def test_get_absolute(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="DAILY")
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
            "Non recurring event test get_occurrence",
            start,
            start + datetime.timedelta(hours=1),
            start + datetime.timedelta(days=10),
            rule,
            cal,
        )
        url = event.get_absolute_url()
        self.assertEqual(reverse("event", kwargs={"event_id": event.id}), url)

    @override_settings(TIME_ZONE="Europe/Helsinki")
    def test_recurring_event_get_occurrence_in_timezone(self):
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        # Event start and end are UTC because that is what is coming
        # from the database
        event = self.__create_recurring_event(
            "Recurrent event test get_occurrence",
            datetime.datetime(2014, 3, 21, 6, 0, tzinfo=pytz.utc),
            datetime.datetime(2014, 3, 21, 8, 0, tzinfo=pytz.utc),
            datetime.datetime(2014, 4, 11, 0, 0, tzinfo=pytz.utc),
            rule,
            cal,
        )
        tzinfo = pytz.timezone("Europe/Helsinki")
        start = tzinfo.localize(datetime.datetime(2014, 3, 28, 8, 0))  # +2
        occurrence = event.get_occurrence(start)
        self.assertEqual(occurrence.start, start)
        occurrence.save()
        # DST change on March 30th from +2 to +3
        start = tzinfo.localize(datetime.datetime(2014, 4, 4, 8, 0))  # +3
        occurrence = event.get_occurrence(start)
        self.assertEqual(occurrence.start, start)

    def test_recurring_event_get_occurrence_different_end_timezone(self):
        end_recurring = datetime.datetime(2016, 7, 30, 11, 0, tzinfo=pytz.utc)

        event = self.__create_recurring_event(
            "Recurring event with end_reccurring_date in different TZ",
            datetime.datetime(2016, 7, 25, 10, 0, tzinfo=pytz.utc),
            datetime.datetime(2016, 7, 25, 11, 0, tzinfo=pytz.utc),
            end_recurring,
            Rule.objects.create(frequency="DAILY"),
            Calendar.objects.create(name="MyCal"),
        )
        tzinfo = pytz.timezone("Europe/Athens")
        occurrences = event.get_occurrences(
            tzinfo.localize(datetime.datetime(2016, 1, 1, 0, 0)),
            tzinfo.localize(datetime.datetime(2016, 12, 31, 23, 59)),
        )
        self.assertEqual(occurrences[-1].end, end_recurring)

    def test_recurring_event_get_occurrence_across_dst(self):

        pacific = pytz.timezone("US/Pacific")
        e_start = pacific.localize(datetime.datetime(2015, 3, 4, 9, 0))
        e_end = e_start
        recc_end = pacific.localize(datetime.datetime(2015, 3, 13, 9, 0))
        event = self.__create_recurring_event(
            "Recurring event with end_recurring_date that crosses a DST",
            e_start,
            e_end,
            recc_end,
            Rule.objects.create(frequency="WEEKLY"),
            Calendar.objects.create(name="MyCal"),
        )
        occs = event.get_occurrences(
            e_start, pacific.localize(datetime.datetime(2015, 3, 11, 10, 0))
        )
        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occs],
            [
                "2015-03-04 09:00:00-08:00 to 2015-03-04 09:00:00-08:00",
                "2015-03-11 09:00:00-07:00 to 2015-03-11 09:00:00-07:00",
            ],
        )

    @override_settings(USE_TZ=False)
    def test_get_occurrences_timespan_inside_occurrence(self):
        """
        Test whether occurrences are correctly obtained if selected timespan start
        and end happen completely inside an occurrence.
        """
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurring event test",
            datetime.datetime(2008, 1, 5, 8, 0),
            datetime.datetime(2008, 1, 5, 9, 0),
            datetime.datetime(2008, 5, 5, 0, 0),
            rule,
            cal,
        )
        occurrences = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 12, 8, 15),
            end=datetime.datetime(2008, 1, 12, 8, 30),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occurrences],
            ["2008-01-12 08:00:00 to 2008-01-12 09:00:00"],
        )

    @override_settings(USE_TZ=False)
    def test_get_occurrences_timespan_partially_inside_occurrence(self):
        """
        Test whether occurrences are correctly obtained if selected timespan start
        outside of timepan but ends inside occurrence.
        """
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurring event test",
            datetime.datetime(2008, 1, 5, 8, 0),
            datetime.datetime(2008, 1, 5, 9, 0),
            datetime.datetime(2008, 5, 5, 0, 0),
            rule,
            cal,
        )

        occs1 = recurring_event.get_occurrences(
            start=datetime.datetime(2006, 1, 1, 0, 0),
            end=datetime.datetime(2008, 1, 19, 8, 30),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occs1],
            [
                "2008-01-05 08:00:00 to 2008-01-05 09:00:00",
                "2008-01-12 08:00:00 to 2008-01-12 09:00:00",
                "2008-01-19 08:00:00 to 2008-01-19 09:00:00",
            ],
        )

        occs2 = recurring_event.get_occurrences(
            start=datetime.datetime(2006, 1, 1, 0, 0),
            end=datetime.datetime(2008, 1, 19, 10, 0),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occs2],
            [
                "2008-01-05 08:00:00 to 2008-01-05 09:00:00",
                "2008-01-12 08:00:00 to 2008-01-12 09:00:00",
                "2008-01-19 08:00:00 to 2008-01-19 09:00:00",
            ],
        )

    @override_settings(USE_TZ=False)
    def test_get_occurrences_timespan_edge_cases(self):
        """
        Test whether occurrence list get method behave when requesting them on
        timespan limits
        """
        cal = Calendar.objects.create(name="MyCal")
        rule = Rule.objects.create(frequency="WEEKLY")

        recurring_event = self.__create_recurring_event(
            "Recurring event test",
            datetime.datetime(2008, 1, 5, 8, 0),
            datetime.datetime(2008, 1, 5, 9, 0),
            datetime.datetime(2008, 5, 5, 0, 0),
            rule,
            cal,
        )

        occs1 = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 5, 8, 0),
            end=datetime.datetime(2008, 1, 5, 8, 30),
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occs1],
            ["2008-01-05 08:00:00 to 2008-01-05 09:00:00"],
        )

        occs2 = recurring_event.get_occurrences(
            start=datetime.datetime(2008, 1, 5, 7, 0),
            end=datetime.datetime(2008, 1, 5, 8, 0),
        )

        self.assertEqual(["{} to {}".format(o.start, o.end) for o in occs2], [])

    @override_settings(USE_TZ=False)
    def test_get_occurrences_rule_weekday_param(self):
        """
        Test whether occurrence list get method behaves correctly while using
        complex rule parameters
        """
        cal = Calendar.objects.create(name="MyCal")
        # Last Fridays of each month
        rule = Rule.objects.create(
            frequency="MONTHLY", params="BYWEEKDAY:FR;BYSETPOS:-1"
        )

        recurring_event = self.__create_recurring_event(
            "Last Friday of each month",
            datetime.datetime(2016, 11, 1),
            datetime.datetime(2016, 11, 1),
            datetime.datetime(2030, 1, 1),
            rule,
            cal,
        )

        occs = recurring_event.get_occurrences(
            start=datetime.datetime(2016, 11, 1), end=datetime.datetime(2017, 12, 31)
        )

        self.assertEqual(
            ["{} to {}".format(o.start, o.end) for o in occs],
            [
                "2016-11-25 00:00:00 to 2016-11-25 00:00:00",
                "2016-12-30 00:00:00 to 2016-12-30 00:00:00",
                "2017-01-27 00:00:00 to 2017-01-27 00:00:00",
                "2017-02-24 00:00:00 to 2017-02-24 00:00:00",
                "2017-03-31 00:00:00 to 2017-03-31 00:00:00",
                "2017-04-28 00:00:00 to 2017-04-28 00:00:00",
                "2017-05-26 00:00:00 to 2017-05-26 00:00:00",
                "2017-06-30 00:00:00 to 2017-06-30 00:00:00",
                "2017-07-28 00:00:00 to 2017-07-28 00:00:00",
                "2017-08-25 00:00:00 to 2017-08-25 00:00:00",
                "2017-09-29 00:00:00 to 2017-09-29 00:00:00",
                "2017-10-27 00:00:00 to 2017-10-27 00:00:00",
                "2017-11-24 00:00:00 to 2017-11-24 00:00:00",
                "2017-12-29 00:00:00 to 2017-12-29 00:00:00",
            ],
        )


class TestEventRelationManager(TestCase):
    def test_get_events_for_object(self):
        pass
