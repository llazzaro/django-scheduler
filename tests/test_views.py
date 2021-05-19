import datetime
import json

import pytz
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence
from schedule.models.rules import Rule
from schedule.settings import USE_FULLCALENDAR
from schedule.views import (
    check_next_url,
    coerce_date_dict,
    get_next_url,
    get_occurrence,
)


class TestViews(TestCase):
    fixtures = ["schedule.json"]

    def setUp(self):
        self.rule = Rule.objects.create(frequency="DAILY")
        self.calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        self.event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=self.rule,
            calendar=self.calendar,
        )

    @override_settings(USE_TZ=False)
    def test_timezone_off(self):
        url = reverse("day_calendar", kwargs={"calendar_slug": self.calendar.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TestViewUtils(TestCase):
    def setUp(self):
        self.rule = Rule.objects.create(frequency="DAILY")
        self.calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        self.event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=self.rule,
            calendar=self.calendar,
        )

    def test_get_occurrence(self):
        event, occurrence = get_occurrence(
            self.event.pk,
            year=2008,
            month=1,
            day=5,
            hour=8,
            minute=0,
            second=0,
            tzinfo=pytz.utc,
        )
        self.assertEqual(event, self.event)
        self.assertEqual(occurrence.start, self.event.start)
        self.assertEqual(occurrence.end, self.event.end)

    def test_get_occurrence_raises(self):
        with self.assertRaises(Http404):
            get_occurrence(
                self.event.pk,
                year=2007,
                month=1,
                day=5,
                hour=8,
                minute=0,
                second=0,
                tzinfo=pytz.utc,
            )

    def test_get_occurrence_persisted(self):
        date = timezone.make_aware(
            datetime.datetime(year=2008, month=1, day=5, hour=8, minute=0, second=0),
            pytz.utc,
        )
        occurrence = self.event.get_occurrence(date)
        occurrence.save()
        with self.assertRaises(Http404):
            get_occurrence(self.event.pk, occurrence_id=100)

        event, persisted_occ = get_occurrence(
            self.event.pk, occurrence_id=occurrence.pk
        )
        self.assertEqual(persisted_occ, occurrence)

    @override_settings(TIME_ZONE="America/Montevideo")
    def test_get_occurrence_raises_wrong_tz(self):
        # Montevideo is 3 hours behind UTC
        with self.assertRaises(Http404):
            event, occurrence = get_occurrence(
                self.event.pk, year=2008, month=1, day=5, hour=8, minute=0, second=0
            )

    def test_coerce_date_dict(self):
        self.assertEqual(
            coerce_date_dict(
                {
                    "year": "2008",
                    "month": "4",
                    "day": "2",
                    "hour": "4",
                    "minute": "4",
                    "second": "4",
                }
            ),
            {"year": 2008, "month": 4, "day": 2, "hour": 4, "minute": 4, "second": 4},
        )

    def test_coerce_date_dict_partial(self):
        self.assertEqual(
            coerce_date_dict({"year": "2008", "month": "4", "day": "2"}),
            {"year": 2008, "month": 4, "day": 2, "hour": 0, "minute": 0, "second": 0},
        )

    def test_coerce_date_dict_empty(self):
        self.assertEqual(coerce_date_dict({}), {})

    def test_coerce_date_dict_missing_values(self):
        self.assertEqual(
            coerce_date_dict({"year": "2008", "month": "4", "hours": "3"}),
            {"year": 2008, "month": 4, "day": 1, "hour": 0, "minute": 0, "second": 0},
        )


class TestGetNextUrl(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_redirects_to_same_server(self):
        redirect_to = "http://testserver/"
        request = self.factory.get(f"?next={redirect_to}")
        self.assertEqual(get_next_url(request, None), redirect_to)

    def test_redirects_to_malicious_server(self):
        request = self.factory.get("?next=http://evil.com")
        self.assertIsNone(get_next_url(request, None))


class TestUrls(TestCase):
    fixtures = ["schedule.json"]
    highest_event_id = 7

    def test_calendar_view(self):
        response = self.client.get(
            reverse("year_calendar", kwargs={"calendar_slug": "example"}), {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]["calendar"].name, "Example Calendar")

    def test_calendar_month_view(self):
        response = self.client.get(
            reverse("month_calendar", kwargs={"calendar_slug": "example"}),
            {"year": 2000, "month": 11},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]["calendar"].name, "Example Calendar")
        month = response.context[0]["period"]
        self.assertEqual(
            (month.start, month.end),
            (
                datetime.datetime(2000, 11, 1, 0, 0, tzinfo=pytz.utc),
                datetime.datetime(2000, 12, 1, 0, 0, tzinfo=pytz.utc),
            ),
        )

    def test_event_creation_anonymous_user(self):
        response = self.client.get(
            reverse("calendar_create_event", kwargs={"calendar_slug": "example"})
        )
        self.assertEqual(response.status_code, 302)

    def test_event_creation_authenticated_user(self):
        self.client.login(username="admin", password="admin")
        response = self.client.get(
            reverse("calendar_create_event", kwargs={"calendar_slug": "example"})
        )

        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("calendar_create_event", kwargs={"calendar_slug": "example"}),
            {
                "description": "description",
                "title": "title",
                "end_recurring_period_1": "10:22:00",
                "end_recurring_period_0": "2008-10-30",
                "end_recurring_period_2": "AM",
                "end_1": "10:22:00",
                "end_0": "2008-10-30",
                "end_2": "AM",
                "start_0": "2008-10-30",
                "start_1": "09:21:57",
                "start_2": "AM",
            },
        )
        self.assertEqual(response.status_code, 302)

        highest_event_id = self.highest_event_id
        highest_event_id += 1
        response = self.client.get(
            reverse("event", kwargs={"event_id": highest_event_id})
        )
        self.assertEqual(response.status_code, 200)

    def test_view_event(self):
        response = self.client.get(reverse("event", kwargs={"event_id": 1}))
        self.assertEqual(response.status_code, 200)

    def test_delete_event_anonymous_user(self):
        # Only logged-in users should be able to delete, so we're redirected
        response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}))
        self.assertEqual(response.status_code, 302)

    def test_delete_event_authenticated_user(self):
        self.client.login(username="admin", password="admin")
        # Load the deletion page
        response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}))
        self.assertEqual(response.status_code, 200)
        if USE_FULLCALENDAR:
            self.assertEqual(
                response.context["next"],
                reverse("fullcalendar", args=[Event.objects.get(id=1).calendar.slug]),
            )
        else:
            self.assertEqual(
                response.context["next"],
                reverse("day_calendar", args=[Event.objects.get(id=1).calendar.slug]),
            )

        # Delete the event
        response = self.client.post(reverse("delete_event", kwargs={"event_id": 1}))
        self.assertEqual(response.status_code, 302)

        # Since the event is now deleted, we get a 404
        response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}))
        self.assertEqual(response.status_code, 404)

    def test_occurrences_api_returns_the_expected_occurrences(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        rule = Rule.objects.create(frequency="DAILY")
        Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=calendar,
        )
        # test calendar slug
        response = self.client.get(
            reverse("api_occurrences")
            + "?calendar={}&start={}&end={}".format(
                "MyCal", datetime.datetime(2008, 1, 5), datetime.datetime(2008, 1, 6)
            )
        )
        self.assertEqual(response.status_code, 200)
        expected_content = [
            {
                "existed": False,
                "end": "2008-01-05T09:00:00Z",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-05-05T00:00:00Z",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-05T08:00:00Z",
                "id": 9,
            }
        ]
        self.assertEqual(json.loads(response.content.decode()), expected_content)

    def test_occurrences_api_without_parameters_return_status_400(self):
        response = self.client.get(reverse("api_occurrences"))
        self.assertEqual(response.status_code, 400)

    def test_occurrences_api_without_calendar_slug_return_status_404(self):
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": datetime.datetime(2008, 1, 5),
                "end": datetime.datetime(2008, 1, 6),
                "calendar_slug": "NoMatch",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_occurrences_api_checks_valid_occurrence_ids(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        rule = Rule.objects.create(frequency="DAILY")
        event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 1, 8, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=calendar,
        )
        Occurrence.objects.create(
            event=event,
            title="My persisted Occ",
            description="Persisted occ test",
            start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            original_start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            original_end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
        )
        # test calendar slug
        response = self.client.get(
            reverse("api_occurrences")
            + "?calendar={}&start={}&end={}".format(
                "MyCal", datetime.datetime(2008, 1, 5), datetime.datetime(2008, 1, 8)
            )
        )
        self.assertEqual(response.status_code, 200)
        expected_content = [
            {
                "existed": False,
                "end": "2008-01-05T09:00:00Z",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-08T00:00:00Z",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-05T08:00:00Z",
                "id": 10,
            },
            {
                "existed": False,
                "end": "2008-01-06T09:00:00Z",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-08T00:00:00Z",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-06T08:00:00Z",
                "id": 10,
            },
            {
                "existed": False,
                "end": "2008-01-07T09:00:00Z",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-08T00:00:00Z",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-07T08:00:00Z",
                "id": 10,
            },
            {
                "existed": True,
                "end": "2008-01-07T08:00:00Z",
                "description": "Persisted occ test",
                "creator": "None",
                "color": "",
                "title": "My persisted Occ",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-08T00:00:00Z",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-07T08:00:00Z",
                "id": 1,
            },
        ]
        self.assertEqual(json.loads(response.content.decode()), expected_content)
        # test timezone param
        response = self.client.get(
            reverse("api_occurrences")
            + "?calendar={}&start={}&end={}&timezone={}".format(
                "MyCal",
                datetime.datetime(2008, 1, 5),
                datetime.datetime(2008, 1, 8),
                "America/Chicago",
            )
        )
        self.assertEqual(response.status_code, 200)
        expected_content = [
            {
                "existed": False,
                "end": "2008-01-05T03:00:00-06:00",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-07T18:00:00-06:00",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-05T02:00:00-06:00",
                "id": 10,
            },
            {
                "existed": False,
                "end": "2008-01-06T03:00:00-06:00",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-07T18:00:00-06:00",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-06T02:00:00-06:00",
                "id": 10,
            },
            {
                "existed": False,
                "end": "2008-01-07T03:00:00-06:00",
                "description": "",
                "creator": "None",
                "color": "",
                "title": "Recent Event",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-07T18:00:00-06:00",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-07T02:00:00-06:00",
                "id": 10,
            },
            {
                "existed": True,
                "end": "2008-01-07T02:00:00-06:00",
                "description": "Persisted occ test",
                "creator": "None",
                "color": "",
                "title": "My persisted Occ",
                "rule": "",
                "event_id": 8,
                "end_recurring_period": "2008-01-07T18:00:00-06:00",
                "cancelled": False,
                "calendar": "MyCalSlug",
                "start": "2008-01-07T02:00:00-06:00",
                "id": 1,
            },
        ]
        self.assertEqual(json.loads(response.content.decode()), expected_content)

    def test_occurrences_api_works_with_and_without_cal_slug(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            calendar=calendar,
        )
        # test calendar slug
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05",
                "end": "2008-02-05",
                "calendar_slug": event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event.title, [d["title"] for d in resp_list])
        # test works with no calendar slug
        response = self.client.get(
            reverse("api_occurrences"), {"start": "2008-01-05", "end": "2008-02-05"}
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event.title, [d["title"] for d in resp_list])

    def test_cal_slug_filters_returned_events(self):
        calendar1 = Calendar.objects.create(name="MyCal1", slug="MyCalSlug1")
        calendar2 = Calendar.objects.create(name="MyCal2", slug="MyCalSlug2")
        event1 = Event.objects.create(
            title="Recent Event 1",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            calendar=calendar1,
        )
        event2 = Event.objects.create(
            title="Recent Event 2",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            calendar=calendar2,
        )
        # Test both present with no cal arg
        response = self.client.get(
            reverse("api_occurrences"), {"start": "2008-01-05", "end": "2008-02-05"}
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event1.title, [d["title"] for d in resp_list])
        self.assertIn(event2.title, [d["title"] for d in resp_list])
        # test event2 not in event1 response
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05",
                "end": "2008-02-05",
                "calendar_slug": event1.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event1.title, [d["title"] for d in resp_list])
        self.assertNotIn(event2.title, [d["title"] for d in resp_list])

    def test_occurrences_api_works_with_different_date_string_formats(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            calendar=calendar,
        )
        # test works with date string time format '%Y-%m-%d'
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05",
                "end": "2008-02-05",
                "calendar_slug": event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event.title, [d["title"] for d in resp_list])
        # test works with date string time format '%Y-%m-%dT%H:%M:%S'
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05T00:00:00",
                "end": "2008-02-05T00:00:00",
                "calendar_slug": event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode())
        self.assertIn(event.title, [d["title"] for d in resp_list])

    def test_occurrences_api_fails_with_incorrect_date_string_formats(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            calendar=calendar,
        )

        # test fails with date string time format not '%Y-%m-%d' or '%Y-%m-%dT%H:%M:%S'
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05T00:00",
                "end": "2008-02-05T00:00",
                "calendar_slug": event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 400)
        resp = response.content.decode()
        expected_error = "does not match format '%Y-%m-%dT%H:%M:%S'"
        self.assertIn(expected_error, resp)

    def test_occurrences_api_filters_cancelled_events(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        weekly_meeting_event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2021, 12, 27, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2021, 12, 27, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2021, 12, 31, 0, 0, tzinfo=pytz.utc),
            calendar=calendar,
        )
        Occurrence.objects.create(
            event=weekly_meeting_event,
            start=weekly_meeting_event.start.replace(year=2021, month=12, day=27),
            end=weekly_meeting_event.end.replace(year=2021, month=12, day=27),
            cancelled=True,
            original_start=weekly_meeting_event.start.replace(
                year=2021, month=12, day=27
            ),
            original_end=weekly_meeting_event.end.replace(year=2021, month=12, day=27),
        )

        # test fails with date string time format not '%Y-%m-%d' or '%Y-%m-%dT%H:%M:%S'
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2021-12-27T08:00:00",
                "end": "2021-12-27T09:00:00",
                "calendar_slug": weekly_meeting_event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        expected_content = []
        self.assertEqual(json.loads(response.content.decode()), expected_content)

    def test_check_next_url_valid_case(self):
        expected = "/calendar/1"
        res = check_next_url("/calendar/1")
        self.assertEqual(expected, res)

    def test_check_next_url_invalid_case(self):
        expected = None
        res = check_next_url("http://localhost/calendar/1")
        self.assertEqual(expected, res)
        res = check_next_url(None)
        self.assertEqual(expected, res)

    @override_settings(SITE_ID=1)
    def test_feed_link(self):
        feed_url = reverse("upcoming_events_feed", kwargs={"calendar_id": 1})
        response = self.client.get(feed_url)
        self.assertEqual(response.status_code, 200)
        expected_feed = "http://example.com/feed/calendar/upcoming/1/"
        self.assertTrue(expected_feed in response.content.decode())

    def test_calendar_view_home(self):
        calendar_view_url = reverse(
            "calendar_home", kwargs={"calendar_slug": "example"}
        )
        response = self.client.get(calendar_view_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            '<a href="/feed/calendar/upcoming/1/">Feed</a>' in response.content.decode()
        )
