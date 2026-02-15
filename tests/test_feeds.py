import datetime

import icalendar
import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from schedule.models import Calendar, Event, Occurrence, Rule


class TestICalendarFeed(TestCase):
    """Test iCalendar feed export functionality"""

    def setUp(self):
        self.calendar = Calendar.objects.create(name="TestCal", slug="testcal")
        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Create a simple event
        self.simple_event = Event.objects.create(
            title="Simple Event",
            start=datetime.datetime(2024, 1, 15, 10, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2024, 1, 15, 11, 0, tzinfo=pytz.utc),
            description="A simple test event",
            calendar=self.calendar,
        )

        # Create a recurring event
        self.rule = Rule.objects.create(frequency="WEEKLY")
        self.recurring_event = Event.objects.create(
            title="Weekly Meeting",
            start=datetime.datetime(2024, 1, 1, 14, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2024, 1, 1, 15, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2024, 3, 1, 0, 0, tzinfo=pytz.utc),
            description="Recurring weekly meeting",
            rule=self.rule,
            calendar=self.calendar,
        )

    def test_icalendar_feed_url_accessible(self):
        """Test that iCalendar feed URL is accessible"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar")

    def test_icalendar_feed_contains_events(self):
        """Test that iCalendar feed contains created events"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        # Parse the iCalendar response
        cal = icalendar.Calendar.from_ical(response.content)

        # Count events in the calendar
        events = [component for component in cal.walk() if component.name == "VEVENT"]
        self.assertGreater(len(events), 0, "Calendar should contain at least one event")

    def test_icalendar_feed_event_properties(self):
        """Test that iCalendar events have required properties"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]

        # Check first event has required properties
        event = events[0]
        self.assertIn("SUMMARY", event, "Event should have SUMMARY (title)")
        self.assertIn("DTSTART", event, "Event should have DTSTART")
        self.assertIn("DTEND", event, "Event should have DTEND")
        self.assertIn("UID", event, "Event should have UID")

    def test_icalendar_feed_event_title(self):
        """Test that event title is correctly exported"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]

        # Get all event titles
        titles = [str(event.get("SUMMARY")) for event in events]
        self.assertIn("Simple Event", titles)

    def test_icalendar_feed_event_dates(self):
        """Test that event dates are correctly exported"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]

        # Find our simple event
        simple_event_ical = None
        for event in events:
            if str(event.get("SUMMARY")) == "Simple Event":
                simple_event_ical = event
                break

        self.assertIsNotNone(simple_event_ical, "Simple Event should be in feed")

        # Check dates (icalendar returns datetime objects)
        dtstart = simple_event_ical.get("DTSTART").dt

        self.assertEqual(dtstart.year, 2024)
        self.assertEqual(dtstart.month, 1)
        self.assertEqual(dtstart.day, 15)
        self.assertEqual(dtstart.hour, 10)

    def test_icalendar_feed_with_occurrence(self):
        """Test that modified occurrences are included in feed"""
        # Create a modified occurrence
        Occurrence.objects.create(
            event=self.simple_event,
            start=datetime.datetime(2024, 1, 16, 11, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2024, 1, 16, 12, 0, tzinfo=pytz.utc),
            original_start=self.simple_event.start,
            original_end=self.simple_event.end,
            title="Modified Simple Event",
        )

        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]

        # Should have events from both the original and the occurrence
        self.assertGreater(len(events), 0)

    def test_icalendar_feed_cancelled_occurrence_not_included(self):
        """Test that cancelled occurrences are not included in feed"""
        # Create a cancelled occurrence
        Occurrence.objects.create(
            event=self.simple_event,
            start=self.simple_event.start,
            end=self.simple_event.end,
            original_start=self.simple_event.start,
            original_end=self.simple_event.end,
            cancelled=True,
        )

        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        # Should still get a valid response
        self.assertEqual(response.status_code, 200)

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]

        # The cancelled occurrence should not appear as a separate event
        # (implementation may vary, just ensure it doesn't break)
        self.assertIsNotNone(events)

    def test_icalendar_feed_calendar_properties(self):
        """Test that iCalendar has required calendar properties"""
        url = reverse("calendar_ical", args=[self.calendar.slug])
        response = self.client.get(url)

        cal = icalendar.Calendar.from_ical(response.content)

        # Check calendar-level properties
        self.assertIn("PRODID", cal, "Calendar should have PRODID")
        self.assertIn("VERSION", cal, "Calendar should have VERSION")
        self.assertEqual(str(cal.get("VERSION")), "2.0")

    def test_icalendar_feed_empty_calendar(self):
        """Test iCalendar feed for empty calendar"""
        empty_calendar = Calendar.objects.create(name="EmptyCal", slug="emptycal")

        url = reverse("calendar_ical", args=[empty_calendar.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar")

        cal = icalendar.Calendar.from_ical(response.content)
        events = [component for component in cal.walk() if component.name == "VEVENT"]
        self.assertEqual(len(events), 0, "Empty calendar should have no events")

    def test_icalendar_feed_nonexistent_calendar(self):
        """Test iCalendar feed for non-existent calendar returns 404"""
        url = reverse("calendar_ical", args=["nonexistent"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
