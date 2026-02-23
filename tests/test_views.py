import datetime
import json
from unittest import mock

from django.contrib.auth.models import User
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
    compress_repeats,
    decode_recurrence_params,
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
            tzinfo=datetime.timezone.utc,
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
                tzinfo=datetime.timezone.utc,
            )

    def test_get_occurrence_persisted(self):
        date = timezone.make_aware(
            datetime.datetime(year=2008, month=1, day=5, hour=8, minute=0, second=0),
            datetime.timezone.utc,
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
                datetime.datetime(2000, 11, 1, 0, 0, tzinfo=datetime.timezone.utc),
                datetime.datetime(2000, 12, 1, 0, 0, tzinfo=datetime.timezone.utc),
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
                "timezone": "UTC",
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
        result = json.loads(response.content.decode())
        self.assertEqual(len(result), 1)
        occ = result[0]
        self.assertEqual(occ["existed"], False)
        self.assertEqual(occ["end"], "2008-01-05T09:00:00Z")
        self.assertEqual(occ["title"], "Recent Event")
        self.assertEqual(occ["start"], "2008-01-05T08:00:00Z")
        self.assertEqual(occ["calendar"], "MyCalSlug")
        self.assertEqual(occ["cancelled"], False)
        self.assertEqual(occ["allDay"], False)
        self.assertEqual(occ["recurrence_frequency"], "DAILY")

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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 1, 8, 0, 0, tzinfo=datetime.timezone.utc
            ),
            rule=rule,
            calendar=calendar,
        )
        Occurrence.objects.create(
            event=event,
            title="My persisted Occ",
            description="Persisted occ test",
            start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=datetime.timezone.utc),
            original_start=datetime.datetime(
                2008, 1, 7, 8, 0, tzinfo=datetime.timezone.utc
            ),
            original_end=datetime.datetime(
                2008, 1, 7, 8, 0, tzinfo=datetime.timezone.utc
            ),
        )
        # test calendar slug
        response = self.client.get(
            reverse("api_occurrences")
            + "?calendar={}&start={}&end={}".format(
                "MyCal", datetime.datetime(2008, 1, 5), datetime.datetime(2008, 1, 8)
            )
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode())
        self.assertEqual(len(result), 4)
        # First 3 are generated occurrences for Jan 5, 6, 7
        self.assertEqual(result[0]["start"], "2008-01-05T08:00:00Z")
        self.assertEqual(result[0]["end"], "2008-01-05T09:00:00Z")
        self.assertFalse(result[0]["existed"])
        self.assertEqual(result[1]["start"], "2008-01-06T08:00:00Z")
        self.assertEqual(result[2]["start"], "2008-01-07T08:00:00Z")
        # 4th is the persisted occurrence
        self.assertTrue(result[3]["existed"])
        self.assertEqual(result[3]["title"], "My persisted Occ")
        self.assertEqual(result[3]["description"], "Persisted occ test")
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
        result_tz = json.loads(response.content.decode())
        self.assertEqual(len(result_tz), 4)
        self.assertEqual(result_tz[0]["start"], "2008-01-05T02:00:00-06:00")
        self.assertEqual(result_tz[0]["end"], "2008-01-05T03:00:00-06:00")
        self.assertEqual(result_tz[3]["title"], "My persisted Occ")

    def test_occurrences_api_works_with_and_without_cal_slug(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendar1,
        )
        event2 = Event.objects.create(
            title="Recent Event 2",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendar,
        )

        # invalid date strings should fail
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "not-a-date",
                "end": "2008-02-05",
                "calendar_slug": event.calendar.slug,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_cal_multiple_slugs_return_all_events(self):
        calendar1 = Calendar.objects.create(name="MyCal1", slug="MyCalSlug1")
        calendar2 = Calendar.objects.create(name="MyCal2", slug="MyCalSlug2")
        calendarOther = Calendar.objects.create(
            name="MyCalOther", slug="MyCalSlugOther"
        )

        event1 = Event.objects.create(
            title="Recent Event 1",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendar1,
        )
        event2 = Event.objects.create(
            title="Recent Event 2",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendar2,
        )

        eventOther = Event.objects.create(
            title="Recent Event Other",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendarOther,
        )

        calendar_slug = ",".join(
            [
                "MyCalSlug1",
                "MyCalSlug2",
            ]
        )

        # Test both present with no cal arg
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05",
                "end": "2008-02-05",
                "calendar_slug": calendar_slug,
            },
        )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode("utf-8"))
        self.assertIn(event1.title, [d["title"] for d in resp_list])
        self.assertIn(event2.title, [d["title"] for d in resp_list])

        self.assertNotIn(eventOther.title, [d["title"] for d in resp_list])

    def test_cal_request_missing_returns_400(self):
        calendar1 = Calendar.objects.create(name="MyCal1", slug="MyCalSlug1")

        Event.objects.create(
            title="Recent Event 1",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            calendar=calendar1,
        )

        calendar_slug = ",".join(
            [
                "MyCalSlug1",
                "MyCalSlugOther",
            ]
        )
        # Test both present with no cal arg
        response = self.client.get(
            reverse("api_occurrences"),
            {
                "start": "2008-01-05",
                "end": "2008-02-05",
                "calendar_slug": calendar_slug,
            },
        )
        self.assertContains(response, "MyCalSlugOther", status_code=400)

    def test_occurrences_api_filters_cancelled_events(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        weekly_meeting_event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2021, 12, 27, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2021, 12, 27, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2021, 12, 31, 0, 0, tzinfo=datetime.timezone.utc
            ),
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
        from django.contrib.sites.models import Site

        Site.objects.update_or_create(
            id=1, defaults={"domain": "testserver", "name": "testserver"}
        )
        feed_url = reverse("upcoming_events_feed", kwargs={"calendar_id": 1})
        response = self.client.get(feed_url)
        self.assertEqual(response.status_code, 200)
        expected_feed = "http://testserver/feed/calendar/upcoming/1/"
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


class TestOccurrencePreview(TestCase):
    def setUp(self):
        self.rule = Rule.objects.create(frequency="DAILY")
        self.calendar = Calendar.objects.create(name="MyCal", slug="MyCalSlug")
        self.event = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 8, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2008, 5, 5, 0, 0, tzinfo=datetime.timezone.utc
            ),
            rule=self.rule,
            calendar=self.calendar,
        )

    def test_generates_preview(self):
        url = reverse(
            "occurrence_by_date",
            kwargs={
                "event_id": self.event.pk,
                "year": 2008,
                "month": 4,
                "day": 20,
                "hour": 8,
                "minute": 30,
                "second": 0,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "schedule/occurrence.html")
        self.assertEqual(response.context["event"], self.event)

        occurrence = response.context["occurrence"]
        self.assertEqual(occurrence.event, self.event)
        self.assertEqual(
            occurrence.start,
            datetime.datetime(2008, 4, 20, 8, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            occurrence.end,
            datetime.datetime(2008, 4, 20, 9, 0, tzinfo=datetime.timezone.utc),
        )


class TestAPIMoveOrResize(TestCase):
    """Test API endpoint for moving and resizing occurrences"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.calendar = Calendar.objects.create(name="TestCal", slug="testcal")
        self.rule = Rule.objects.create(frequency="DAILY")

        self.event = Event.objects.create(
            title="Test Event",
            start=datetime.datetime(2024, 1, 15, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2024, 1, 15, 11, 0, tzinfo=datetime.timezone.utc),
            end_recurring_period=datetime.datetime(
                2024, 1, 20, 0, 0, tzinfo=datetime.timezone.utc
            ),
            rule=self.rule,
            calendar=self.calendar,
            creator=self.user,
        )

        # Create a persisted occurrence
        self.occurrence = Occurrence.objects.create(
            event=self.event,
            start=datetime.datetime(2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc),
            original_start=datetime.datetime(
                2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc
            ),
            original_end=datetime.datetime(
                2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def test_api_move_occurrence_authenticated(self):
        """Test moving a persisted occurrence with authenticated user"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": self.occurrence.id,
                "existed": "true",
                "delta": "60",  # Move 1 hour forward (60 minutes)
                "resize": "false",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")

        # Verify the occurrence was moved
        self.occurrence.refresh_from_db()
        self.assertEqual(
            self.occurrence.start,
            datetime.datetime(2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            self.occurrence.end,
            datetime.datetime(2024, 1, 16, 12, 0, tzinfo=datetime.timezone.utc),
        )

    def test_api_resize_occurrence_authenticated(self):
        """Test resizing a persisted occurrence with authenticated user"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": self.occurrence.id,
                "existed": "true",
                "delta": "30",  # Extend by 30 minutes
                "resize": "true",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")

        # Verify the occurrence was resized (only end should change)
        self.occurrence.refresh_from_db()
        self.assertEqual(
            self.occurrence.start,
            datetime.datetime(2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            self.occurrence.end,
            datetime.datetime(2024, 1, 16, 11, 30, tzinfo=datetime.timezone.utc),
        )

    def test_api_move_event_authenticated(self):
        """Test moving a non-persisted event occurrence"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": "999999",  # Non-existent occurrence ID
                "existed": "false",
                "delta": "60",  # Move 1 hour forward
                "resize": "false",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")

        # Verify the event itself was moved
        self.event.refresh_from_db()
        self.assertEqual(
            self.event.start,
            datetime.datetime(2024, 1, 15, 11, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            self.event.end,
            datetime.datetime(2024, 1, 15, 12, 0, tzinfo=datetime.timezone.utc),
        )

    def test_api_resize_event_authenticated(self):
        """Test resizing a non-persisted event"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": "999999",
                "existed": "false",
                "delta": "30",
                "resize": "true",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")

        # Verify only the event end was extended
        self.event.refresh_from_db()
        self.assertEqual(
            self.event.start,
            datetime.datetime(2024, 1, 15, 10, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            self.event.end,
            datetime.datetime(2024, 1, 15, 11, 30, tzinfo=datetime.timezone.utc),
        )

    @mock.patch("schedule.views.CHECK_OCCURRENCE_PERM_FUNC", return_value=False)
    def test_api_move_occurrence_permission_denied(self, mock_perm):
        """Test that permission check prevents unauthorized moves"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": self.occurrence.id,
                "existed": "true",
                "delta": "60",
                "resize": "false",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "PERMISSION DENIED")

        # Verify the occurrence was NOT moved
        self.occurrence.refresh_from_db()
        self.assertEqual(
            self.occurrence.start,
            datetime.datetime(2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc),
        )

    @mock.patch("schedule.views.CHECK_EVENT_PERM_FUNC", return_value=False)
    def test_api_move_event_permission_denied(self, mock_perm):
        """Test that permission check prevents unauthorized event moves"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": "999999",
                "existed": "false",
                "delta": "60",
                "resize": "false",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "PERMISSION DENIED")

        # Verify the event was NOT moved
        self.event.refresh_from_db()
        self.assertEqual(
            self.event.start,
            datetime.datetime(2024, 1, 15, 10, 0, tzinfo=datetime.timezone.utc),
        )

    def test_api_move_negative_delta(self):
        """Test moving occurrence backward in time"""
        self.client.login(username="testuser", password="testpass")

        url = reverse("api_move_or_resize")
        response = self.client.post(
            url,
            {
                "id": self.occurrence.id,
                "existed": "true",
                "delta": "-30",  # Move 30 minutes earlier
                "resize": "false",
                "event_id": self.event.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")

        # Verify the occurrence was moved backward
        self.occurrence.refresh_from_db()
        self.assertEqual(
            self.occurrence.start,
            datetime.datetime(2024, 1, 16, 9, 30, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            self.occurrence.end,
            datetime.datetime(2024, 1, 16, 10, 30, tzinfo=datetime.timezone.utc),
        )


class TestAPICrud(TestCase):
    """Test CRUD API endpoints for FullCalendar integration"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.calendar = Calendar.objects.create(name="TestCal", slug="testcal")
        self.event = Event.objects.create(
            title="Test Event",
            start=datetime.datetime(2024, 1, 15, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2024, 1, 15, 11, 0, tzinfo=datetime.timezone.utc),
            calendar=self.calendar,
            creator=self.user,
        )

    def test_api_select_create(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("api_select_create"),
            {
                "start": "2024-02-01T10:00:00+00:00",
                "end": "2024-02-01T11:00:00+00:00",
                "calendar_slug": "testcal",
                "title": "New Event",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        self.assertIn("event_id", data)
        event = Event.objects.get(id=data["event_id"])
        self.assertEqual(event.title, "New Event")

    def test_api_select_create_with_timezone(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("api_select_create"),
            {
                "start": "2024-02-01T10:00:00+00:00",
                "end": "2024-02-01T11:00:00+00:00",
                "calendar_slug": "testcal",
                "title": "TZ Event",
                "timezone": "Europe/Vienna",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        event = Event.objects.get(id=data["event_id"])
        self.assertEqual(event.timezone, "Europe/Vienna")

    def test_api_select_create_unauthenticated(self):
        response = self.client.post(
            reverse("api_select_create"),
            {
                "start": "2024-02-01T10:00:00+00:00",
                "end": "2024-02-01T11:00:00+00:00",
                "calendar_slug": "testcal",
                "title": "Fail",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_api_delete_event(self):
        self.client.login(username="testuser", password="testpass")
        event_id = self.event.id
        response = self.client.post(
            reverse("api_delete"),
            {
                "event_id": event_id,
                "existed": "false",
                "calendar_slug": "testcal",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        self.assertFalse(Event.objects.filter(id=event_id).exists())

    def test_api_delete_occurrence(self):
        self.client.login(username="testuser", password="testpass")
        occurrence = Occurrence.objects.create(
            event=self.event,
            start=datetime.datetime(2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc),
            original_start=datetime.datetime(
                2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc
            ),
            original_end=datetime.datetime(
                2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )
        response = self.client.post(
            reverse("api_delete"),
            {
                "id": occurrence.id,
                "existed": "true",
                "calendar_slug": "testcal",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        self.assertFalse(Occurrence.objects.filter(id=occurrence.id).exists())

    @mock.patch("schedule.views.CHECK_EVENT_PERM_FUNC", return_value=False)
    def test_api_delete_permission_denied(self, mock_perm):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("api_delete"),
            {
                "event_id": self.event.id,
                "existed": "false",
                "calendar_slug": "testcal",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "PERMISSION DENIED")
        self.assertTrue(Event.objects.filter(id=self.event.id).exists())

    def test_api_set_props_title(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("api_set_props"),
            {
                "event_id": self.event.id,
                "existed": "false",
                "calendar_slug": "testcal",
                "prop_title": "Updated Title",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Title")
        self.assertEqual(self.event.updater, self.user)

    def test_api_set_props_on_occurrence(self):
        self.client.login(username="testuser", password="testpass")
        occurrence = Occurrence.objects.create(
            event=self.event,
            start=datetime.datetime(2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc),
            original_start=datetime.datetime(
                2024, 1, 16, 10, 0, tzinfo=datetime.timezone.utc
            ),
            original_end=datetime.datetime(
                2024, 1, 16, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )
        response = self.client.post(
            reverse("api_set_props"),
            {
                "id": occurrence.id,
                "existed": "true",
                "calendar_slug": "testcal",
                "prop_title": "Occ Title",
                "prop_description": "Occ Desc",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        occurrence.refresh_from_db()
        self.assertEqual(occurrence.title, "Occ Title")
        self.assertEqual(occurrence.description, "Occ Desc")

    @mock.patch("schedule.views.CHECK_EVENT_PERM_FUNC", return_value=False)
    def test_api_set_props_permission_denied(self, mock_perm):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("api_set_props"),
            {
                "event_id": self.event.id,
                "existed": "false",
                "calendar_slug": "testcal",
                "prop_title": "Should Not Change",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "PERMISSION DENIED")
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Test Event")

    def test_api_ruleparams(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("api_ruleparams"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data["status"], "OK")
        self.assertIn("ruleparams", data)
        names = {rp["name"] for rp in data["ruleparams"]}
        self.assertIn("byweekday", names)
        self.assertIn("bymonth", names)


class TestHelpers(TestCase):
    def test_decode_recurrence_params(self):
        data = {
            "recurrence_byweekday": "0,1",
            "recurrence_bymonth": "1,6",
            "other_key": "ignored",
            "recurrence_bysetpos": "",
        }
        result = decode_recurrence_params(data)
        self.assertEqual(result["byweekday"], [0, 1])
        self.assertEqual(result["bymonth"], [1, 6])
        self.assertNotIn("bysetpos", result)
        self.assertNotIn("other_key", result)

    def test_compress_repeats(self):
        repeats = [
            ("bymonthday", 1),
            ("bymonthday", 2),
            ("byweekday", 0),
        ]
        result = compress_repeats(repeats)
        self.assertEqual(result["bymonthday"], [1, 2])
        self.assertEqual(result["byweekday"], [0])


class TestColorInputWidget(TestCase):
    def test_color_input_render(self):
        from schedule.widgets import ColorInput

        widget = ColorInput()
        html = widget.render("color_field", "#ff0000")
        self.assertIn('type="color"', html)
        self.assertIn("#ff0000", html)
