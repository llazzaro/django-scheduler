import os, datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test import Client

from schedule.views import check_next_url, coerce_date_dict
from schedule.templatetags.scheduletags import querystring_for_date

class TestViewUtils(TestCase):

    def test_check_next_url(self):
        url = "http://thauber.com"
        self.assertTrue(check_next_url(url) is None)
        url = "/hello/world/"
        self.assertEqual(url, check_next_url(url))

    def test_coerce_date_dict(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'day': '2', 'hour': '4', 'minute': '4', 'second': '4'}),
            {'year': 2008, 'month': 4, 'day': 2, 'hour': 4, 'minute': 4, 'second': 4}
            )

    def test_coerce_date_dict_partial(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'day': '2'}),
            {'year': 2008, 'month': 4, 'day': 2, 'hour': 0, 'minute': 0, 'second': 0}
            )

    def test_coerce_date_dict_empty(self):
        self.assertEqual(
            coerce_date_dict({}),
            {}
            )

    def test_coerce_date_dict_missing_values(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'hours': '3'}),
            {'year': 2008, 'month': 4, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0}
            )


c = Client()

class TestUrls(TestCase):

    fixtures = ['schedule.json']
    highest_event_id = 7

    def test_calendar_view(self):
        self.response = c.get(
            reverse("year_calendar", kwargs={"calendar_slug":'example'}), {})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "Example Calendar")

    def test_calendar_month_view(self):
        self.response = c.get(reverse("month_calendar",
                                      kwargs={"calendar_slug":'example'}),
                              {'year': 2000, 'month': 11})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "Example Calendar")
        month = self.response.context[0]["periods"]['month']
        self.assertEqual((month.start, month.end),
                         (datetime.datetime(2000, 11, 1, 0, 0), datetime.datetime(2000, 12, 1, 0, 0)))

    def test_event_creation_anonymous_user(self):
        self.response = c.get(reverse("calendar_create_event",
                                      kwargs={"calendar_slug":'example'}),
                              {})
        self.assertEqual(self.response.status_code, 302)

    def test_event_creation_authenticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get(reverse("calendar_create_event",
                                      kwargs={"calendar_slug":'example'}),
                              {})
        self.assertEqual(self.response.status_code, 200)

        self.response = c.post(reverse("calendar_create_event",
                                      kwargs={"calendar_slug":'example'}),
                               {'description': 'description',
                                'title': 'title',
                                'end_recurring_period_1': '10:22:00','end_recurring_period_0': '2008-10-30', 'end_recurring_period_2': 'AM',
                                'end_1': '10:22:00','end_0': '2008-10-30', 'end_2': 'AM',
                                'start_0': '2008-10-30','start_1': '09:21:57', 'start_2': 'AM'
                               })
        self.assertEqual(self.response.status_code, 302)

        highest_event_id = self.highest_event_id
        highest_event_id += 1
        self.response = c.get(reverse("event",
                                      kwargs={"event_id":highest_event_id}), {})
        self.assertEqual(self.response.status_code, 200)
        c.logout()

    def test_view_event(self):
        self.response = c.get(reverse("event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)

    def test_delete_event_anonymous_user(self):
        # Only logged-in users should be able to delete, so we're redirected
        self.response = c.get(reverse("delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)

    def test_delete_event_authenticated_user(self):
        c.login(username="admin", password="admin")

        # Load the deletion page
        self.response = c.get(reverse("delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)

        # Delete the event
        self.response = c.post(reverse("delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)

        # Since the event is now deleted, we get a 404
        self.response = c.get(reverse("delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 404)
        c.logout()

