import datetime

from django.test import TestCase
from django.utils import timezone

from schedule.models import Calendar, CalendarRelation, Event, Rule


class TestCalendarInheritance(TestCase):
    def test_get_or_create_calendar_for_object_when_proxy_calendar_should_return_proxy_calendar(
        self,
    ):
        class ProxyCalendar(Calendar):
            class Meta:
                proxy = True

        rule = Rule.objects.create()
        self.assertIsInstance(
            ProxyCalendar.objects.get_or_create_calendar_for_object(rule), ProxyCalendar
        )


class TestCalendar(TestCase):
    def test_get_recent_events_without_events_is_empty(self):
        calendar = Calendar()
        calendar.save()
        self.assertEqual(list(calendar.get_recent()), [])

    def test_get_recent_events_with_events_return_the_event(self):
        pass

    def test_occurrences_after_without_events_is_empty(self):
        calendar = Calendar()
        calendar.save()
        self.assertEqual(list(calendar.occurrences_after(timezone.now())), [])

    def test_occurrences_after_with_events_after_returns_events(self):
        calendar = Calendar.objects.create()
        start_after = timezone.now() + datetime.timedelta(days=1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = Event.objects.create(
            title="Recent Event", start=start_after, end=end_after, calendar=calendar
        )
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].start, start_after)
        self.assertEqual(occurrences[0].end, end_after)

    def test_occurrences_after_with_events_before_returns_empty(self):
        calendar = Calendar.objects.create()
        start_after = timezone.now() + datetime.timedelta(days=-1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = Event.objects.create(
            title="Recent Event", start=start_after, end=end_after, calendar=calendar
        )
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEqual(occurrences, [])

    def test_get_calendar_for_object(self):
        calendar = Calendar.objects.create(name="My Cal")
        rule = Rule.objects.create()
        calendar.create_relation(rule)
        result = Calendar.objects.get_calendar_for_object(rule)
        self.assertEqual(result.name, "My Cal")

    def test_get_calendar_for_object_without_calendars(self):
        with self.assertRaises(Calendar.DoesNotExist):
            rule = Rule.objects.create()
            Calendar.objects.get_calendar_for_object(rule)

    def test_get_calendar_for_object_with_more_than_one_calendar(self):
        calendar_1 = Calendar.objects.create(name="My Cal 1", slug="my-cal-1")
        calendar_2 = Calendar.objects.create(name="My Cal 2", slug="my-cal-2")
        rule = Rule.objects.create()
        calendar_1.create_relation(rule)
        calendar_2.create_relation(rule)
        with self.assertRaises(AssertionError):
            Calendar.objects.get_calendar_for_object(rule)

    def test_get_or_create_calendar_for_object_without_calendar(self):
        """
        Creation test
        """
        rule = Rule.objects.create()
        calendar = Calendar.objects.get_or_create_calendar_for_object(
            rule, name="My Cal"
        )
        self.assertEqual(calendar.name, "My Cal")
        calendar_from_rule = Calendar.objects.get_calendars_for_object(rule)[0]
        self.assertEqual(calendar, calendar_from_rule)

    def test_get_or_create_calendar_for_object_withouth_name(self):
        """
        Test with already created calendar
        """
        rule = Rule.objects.create()
        calendar = Calendar.objects.get_or_create_calendar_for_object(rule)
        calendar_from_rule = Calendar.objects.get_calendars_for_object(rule)[0]
        self.assertEqual(calendar, calendar_from_rule)

    def test_get_calendars_for_object_without_calendars(self):
        rule = Rule.objects.create()
        Calendar.objects.get_or_create_calendar_for_object(
            rule, name="My Cal", distinction="owner"
        )
        rule = Rule.objects.create()
        calendars = list(
            Calendar.objects.get_calendars_for_object(rule, distinction="owner")
        )
        self.assertEqual(len(calendars), 0)

    def test_calendar_absolute_and_event_url(self):
        """
        this test seems to not make too much send, just added since an
        url was with wrong reverse name.

        """
        rule = Rule.objects.create()
        calendar = Calendar.objects.get_or_create_calendar_for_object(
            rule, name="My Cal", distinction="owner"
        )
        calendar.get_absolute_url()
        CalendarRelation.objects.create_relation(calendar, rule)
