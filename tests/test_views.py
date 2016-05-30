import datetime
import json
import pytz

from django.test.utils import override_settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence
from schedule.models.rules import Rule

from schedule.views import coerce_date_dict

from schedule.conf.settings import USE_FULLCALENDAR


class TestViews(TestCase):
    fixtures = ['schedule.json']

    def setUp(self):
        self.rule = Rule.objects.create(frequency="DAILY")
        self.calendar = Calendar.objects.create(name="MyCal", slug='MyCalSlug')
        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': self.rule,
            'calendar': self.calendar
        }
        self.event = Event.objects.create(**data)

    @override_settings(USE_TZ=False)
    def test_timezone_off(self):
        url = reverse('day_calendar', kwargs={'calendar_slug': self.calendar.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.login(username="admin", password="admin")


class TestViewUtils(TestCase):
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


class TestUrls(TestCase):
    fixtures = ['schedule.json']
    highest_event_id = 7

    def test_calendar_view(self):
        self.response = self.client.get(
            reverse("year_calendar", kwargs={"calendar_slug": 'example'}), {})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "Example Calendar")

    def test_calendar_month_view(self):
        self.response = self.client.get(reverse("month_calendar",
                                      kwargs={"calendar_slug": 'example'}),
                              {'year': 2000, 'month': 11})
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context[0]["calendar"].name,
                         "Example Calendar")
        month = self.response.context[0]["period"]
        self.assertEqual((month.start, month.end),
                         (datetime.datetime(2000, 11, 1, 0, 0, tzinfo=pytz.utc),
                          datetime.datetime(2000, 12, 1, 0, 0, tzinfo=pytz.utc)))

    def test_event_creation_anonymous_user(self):
        self.response = self.client.get(reverse("calendar_create_event",
                                      kwargs={"calendar_slug": 'example'}), {})
        self.assertEqual(self.response.status_code, 302)

    def test_event_creation_authenticated_user(self):
        self.client.login(username="admin", password="admin")
        self.response = self.client.get(reverse("calendar_create_event",
                                      kwargs={"calendar_slug": 'example'}), {})

        self.assertEqual(self.response.status_code, 200)

        self.response = self.client.post(reverse("calendar_create_event",
                                       kwargs={"calendar_slug": 'example'}),
                                       {'description': 'description',
                                        'title': 'title',
                                        'end_recurring_period_1': '10:22:00', 'end_recurring_period_0': '2008-10-30',
                                        'end_recurring_period_2': 'AM',
                                        'end_1': '10:22:00', 'end_0': '2008-10-30', 'end_2': 'AM',
                                        'start_0': '2008-10-30', 'start_1': '09:21:57', 'start_2': 'AM'})
        self.assertEqual(self.response.status_code, 302)

        highest_event_id = self.highest_event_id
        highest_event_id += 1
        self.response = self.client.get(reverse("event",
                                      kwargs={"event_id": highest_event_id}), {})
        self.assertEqual(self.response.status_code, 200)
        self.client.logout()

    def test_view_event(self):
        self.response = self.client.get(reverse("event", kwargs={"event_id": 1}), {})
        self.assertEqual(self.response.status_code, 200)

    def test_delete_event_anonymous_user(self):
        # Only logged-in users should be able to delete, so we're redirected
        self.response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}), {})
        self.assertEqual(self.response.status_code, 302)

    def test_delete_event_authenticated_user(self):
        self.client.login(username="admin", password="admin")
        # Load the deletion page
        self.response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}), {})
        self.assertEqual(self.response.status_code, 200)
        if USE_FULLCALENDAR:
            self.assertEqual(self.response.context['next'],
                         reverse('fullcalendar', args=[Event.objects.get(id=1).calendar.slug]))
        else:
            self.assertEqual(self.response.context['next'],
                         reverse('day_calendar', args=[Event.objects.get(id=1).calendar.slug]))

        # Delete the event
        self.response = self.client.post(reverse("delete_event", kwargs={"event_id": 1}), {})
        self.assertEqual(self.response.status_code, 302)

        # Since the event is now deleted, we get a 404
        self.response = self.client.get(reverse("delete_event", kwargs={"event_id": 1}), {})
        self.assertEqual(self.response.status_code, 404)
        self.client.logout()

    def test_occurences_api_returns_the_expected_occurences(self):
        # create a calendar and event
        self.calendar = Calendar.objects.create(name="MyCal", slug='MyCalSlug')
        self.rule = Rule.objects.create(frequency="DAILY")
        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': self.rule,
            'calendar': self.calendar
        }
        self.event = Event.objects.create(**data)
        # test calendar slug
        self.response = self.client.get(reverse("api_occurences") +
                                        "?calendar={}&start={}&end={}".format(
                                            'MyCal',
                                            datetime.datetime(2008, 1, 5),
                                            datetime.datetime(2008, 1, 6)
                                        ))
        self.assertEqual(self.response.status_code, 200)
        expected_content = [{u'existed': False, u'end': u'2008-01-05T09:00:00+00:00', u'description': None, u'creator': u'None', u'color': None, u'title': u'Recent Event', u'rule': u'', u'event_id': 8, u'end_recurring_period': u'2008-05-05T00:00:00+00:00', u'cancelled': False, u'calendar': u'MyCalSlug', u'start': u'2008-01-05T08:00:00+00:00', u'id': 9}]
        self.assertEquals(json.loads(self.response.content.decode()), expected_content)

    def test_occurences_api_without_parameters_return_status_400(self):
        self.response = self.client.get(reverse("api_occurences"))
        self.assertEqual(self.response.status_code, 400)

    def test_occurrences_api_without_calendar_slug_return_status_404(self):
        self.response = self.client.get(reverse("api_occurences"),
                                        {'start': datetime.datetime(2008, 1, 5),
                                         'end': datetime.datetime(2008, 1, 6),
                                         'calendar_slug': 'NoMatch'})
        self.assertEqual(self.response.status_code, 400)

    def test_occurences_api_checks_valid_occurrence_ids(self):
        # create a calendar and event
        self.calendar = Calendar.objects.create(name="MyCal", slug='MyCalSlug')
        self.rule = Rule.objects.create(frequency="DAILY")
        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 1, 8, 0, 0, tzinfo=pytz.utc),
            'rule': self.rule,
            'calendar': self.calendar
        }
        self.event = Event.objects.create(**data)
        Occurrence.objects.create(
            event=self.event,
            title='My persisted Occ',
            description='Persisted occ test',
            start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            original_start=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
            original_end=datetime.datetime(2008, 1, 7, 8, 0, tzinfo=pytz.utc),
        )
        # test calendar slug
        self.response = self.client.get(reverse("api_occurences") +
                                        "?calendar={}&start={}&end={}".format(
                                            'MyCal',
                                            datetime.datetime(2008, 1, 5),
                                            datetime.datetime(2008, 1, 8)
                                        ))
        self.assertEqual(self.response.status_code, 200)
        expected_content = [{u'existed': False, u'end': u'2008-01-05T09:00:00+00:00', u'description': None, u'creator': u'None', u'color': None, u'title': u'Recent Event', u'rule': u'', u'event_id': 8, u'end_recurring_period': u'2008-01-08T00:00:00+00:00', u'cancelled': False, u'calendar': u'MyCalSlug', u'start': u'2008-01-05T08:00:00+00:00', u'id': 10}, {u'existed': False, u'end': u'2008-01-06T09:00:00+00:00', u'description': None, u'creator': u'None', u'color': None, u'title': u'Recent Event', u'rule': u'', u'event_id': 8, u'end_recurring_period': u'2008-01-08T00:00:00+00:00', u'cancelled': False, u'calendar': u'MyCalSlug', u'start': u'2008-01-06T08:00:00+00:00', u'id': 10}, {u'existed': False, u'end': u'2008-01-07T09:00:00+00:00', u'description': None, u'creator': u'None', u'color': None, u'title': u'Recent Event', u'rule': u'', u'event_id': 8, u'end_recurring_period': u'2008-01-08T00:00:00+00:00', u'cancelled': False, u'calendar': u'MyCalSlug', u'start': u'2008-01-07T08:00:00+00:00', u'id': 10}, {u'existed': True, u'end': u'2008-01-07T08:00:00+00:00', u'description': u'Persisted occ test', u'creator': u'None', u'color': None, u'title': u'My persisted Occ', u'rule': u'', u'event_id': 8, u'end_recurring_period': u'2008-01-08T00:00:00+00:00', u'cancelled': False, u'calendar': u'MyCalSlug', u'start': u'2008-01-07T08:00:00+00:00', u'id': 1}]
        self.assertEquals(json.loads(self.response.content.decode()), expected_content)

    def test_occurences_api_works_with_and_without_cal_slug(self):
        # create a calendar and event
        calendar = Calendar.objects.create(name="MyCal", slug='MyCalSlug')
        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'calendar': calendar
        }
        event = Event.objects.create(**data)
        # test calendar slug
        response = self.client.get(reverse('api_occurences'),
                                         {'start': '2008-01-05',
                                         'end': '2008-02-05',
                                         'calendar_slug': event.calendar.slug})
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode('utf-8'))
        self.assertIn(event.title, [d['title'] for d in resp_list])
        # test works with no calendar slug
        response = self.client.get(reverse("api_occurences"),
                                   {'start': '2008-01-05',
                                    'end': '2008-02-05'
                                    })
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode('utf-8'))
        self.assertIn(event.title, [d['title'] for d in resp_list])

    def test_cal_slug_filters_returned_events(self):
        calendar1 = Calendar.objects.create(name="MyCal1", slug='MyCalSlug1')
        calendar2 = Calendar.objects.create(name="MyCal2", slug='MyCalSlug2')
        data1 = {
            'title': 'Recent Event 1',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'calendar': calendar1
        }
        data2 = {
            'title': 'Recent Event 2',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'calendar': calendar2
        }
        event1 = Event.objects.create(**data1)
        event2 = Event.objects.create(**data2)
        # Test both present with no cal arg
        response = self.client.get(reverse("api_occurences"),
                                   {'start': '2008-01-05',
                                   'end': '2008-02-05'}
                                   )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode('utf-8'))
        self.assertIn(event1.title, [d['title'] for d in resp_list])
        self.assertIn(event2.title, [d['title'] for d in resp_list])
        # test event2 not in event1 response
        response = self.client.get(reverse("api_occurences"),
                                    {'start': '2008-01-05',
                                     'end': '2008-02-05',
                                     'calendar_slug': event1.calendar.slug}
                                   )
        self.assertEqual(response.status_code, 200)
        resp_list = json.loads(response.content.decode('utf-8'))
        self.assertIn(event1.title, [d['title'] for d in resp_list])
        self.assertNotIn(event2.title, [d['title'] for d in resp_list])
