import os
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase

c = Client()

class TestUrls(TestCase):
    schedule_fixture = os.path.join(getattr(settings, 'PROJECT_DIR'),
                                    "fixtures/schedule.json")

    fixtures = [schedule_fixture]

    def test_calendar_view(self):
        self.response = c.get(reverse("s_calendar", kwargs={"calendar_id":1}), {})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "work")

    def test_calendar_date_view(self):
        self.response = c.get(reverse("s_calendar_date",
                                      kwargs={
                                        "calendar_id":1,
                                        "year":2008,
                                        "month":11
                                        }),
                              {})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "work")
        month = self.response.context[0]["month"]
        self.assertEqual((month.start,month.end),
                         (datetime.datetime(2008, 11, 1, 0, 0), datetime.datetime(2008, 12, 1, 0, 0)))

    def test_event_creation_anonymous_user(self):
        self.response = c.get(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                              {})
        self.assertEqual(self.response.status_code, 302)

    def test_event_creation_authenticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                              {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                               {'description': 'description',
                                'title': 'title',
                                'end_recurring_period_1': '10:22:00','end_recurring_period_0': '2008-10-30', 'end_recurring_period_2': 'AM',
                                'end_1': '10:22:00','end_0': '2008-10-30', 'end_2': 'AM',
                                'start_0': '2008-10-30','start_1': '09:21:57', 'start_2': 'AM'
                               })
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get(reverse("s_event",kwargs={"event_id":2}), {})
        self.assertEqual(self.response.status_code, 200)
        c.logout()

    def test_view_event(self):
        self.response = c.get(reverse("s_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)

    def test_delete_event_anonymous_user(self):
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)

    def test_delete_event_authenticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 404)
        c.logout()
