import datetime
import os

from django.test import TestCase
from django.test import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from schedule.forms import GlobalSplitDateTimeWidget
from schedule.models import Event, Rule
from schedule.occurrence import Occurrence
from schedule.periods import Period, Month


class TestSplitDateTimeWidget(TestCase):
    def setUp(self):
        self.widget = GlobalSplitDateTimeWidget()
        self.value = datetime.datetime(2008, 1, 1, 5, 5)
        self.data = {'datetime_0':'2008-1-1', 'datetime_1':'5:05', 'datetime_2': 'PM'}
    def test_widget_decompress(self):
        self.assertEquals(self.widget.decompress(self.value),
                          [datetime.date(2008, 1, 1), '05:05', 'AM'])

    def test_widget_value_from_datadict(self):
        self.assertEquals(self.widget.value_from_datadict(self.data, None, 'datetime'),
                          datetime.datetime(2008, 1, 1, 17, 5))
        widget = GlobalSplitDateTimeWidget(hour24 = True)
        self.assertEquals(widget.value_from_datadict(self.data, None, 'datetime'),
                          ['2008-1-1', '5:05'])

class TestOccurrence(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        self.recurring_data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        self.data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
               }
    def test_recurring_event_get_occurrences(self):
        recurring_event = Event(**self.recurring_data)
        recurring_event.save()
        occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0),
                                    end=datetime.datetime(2008, 1, 20, 0, 0))
        self.assertEquals(["%s to %s" %(o.start, o.end) for o in occurrences],
            ['2008-01-12 08:00:00 to 2008-01-12 09:00:00', '2008-01-19 08:00:00 to 2008-01-19 09:00:00'])

    def test_event_get_occurrences(self):
        event= Event(**self.data)
        event.save()
        occurrences = event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0),
                                    end=datetime.datetime(2008, 1, 20, 0, 0))

        self.assertEquals(["%s to %s" %(o.start, o.end) for o in occurrences],
            [])

class TestPeriod(TestCase):

    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        recurring_event = Event(**data)
        recurring_event.save()
        self.period = Period(events=Event.objects.all(),
                            start = datetime.datetime(2008,1,4,7,0),
                            end = datetime.datetime(2008,1,21,7,0))
    def test_get_occurences(self):
        occurrence_list = self.period.occurrences
        self.assertEqual(["%s to %s" %(o.start, o.end) for o in occurrence_list],
            ['2008-01-05 08:00:00 to 2008-01-05 09:00:00',
             '2008-01-12 08:00:00 to 2008-01-12 09:00:00',
             '2008-01-19 08:00:00 to 2008-01-19 09:00:00'])

    def test_get_occurrence_partials(self):
        occurrence_dicts = self.period.get_occurrence_partials()
        self.assertEqual(
            [(occ_dict["class"],
            occ_dict["occurrence"].start,
            occ_dict["occurrence"].end)
            for occ_dict in occurrence_dicts],
            [
                (1,
                 datetime.datetime(2008, 1, 5, 8, 0),
                 datetime.datetime(2008, 1, 5, 9, 0)),
                (1,
                 datetime.datetime(2008, 1, 12, 8, 0),
                 datetime.datetime(2008, 1, 12, 9, 0)),
                (1,
                 datetime.datetime(2008, 1, 19, 8, 0),
                 datetime.datetime(2008, 1, 19, 9, 0))
            ])

class TestMonth(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        recurring_event = Event(**data)
        recurring_event.save()
        self.month = Month(events=Event.objects.all(),
                           date=datetime.datetime(2008, 2, 7, 9, 0))
    def test_get_weeks(self):
        weeks = self.month.get_weeks()
        self.assertEqual([(week.start,week.end) for week in weeks],
            [
                (datetime.datetime(2008, 1, 27, 0, 0),
                datetime.datetime(2008, 2, 3, 0, 0)),
                (datetime.datetime(2008, 2, 3, 0, 0),
                datetime.datetime(2008, 2, 10, 0, 0)),
                (datetime.datetime(2008, 2, 10, 0, 0),
                 datetime.datetime(2008, 2, 17, 0, 0)),
                (datetime.datetime(2008, 2, 17, 0, 0),
                 datetime.datetime(2008, 2, 24, 0, 0)),
                (datetime.datetime(2008, 2, 24, 0, 0),
                 datetime.datetime(2008, 3, 2, 0, 0))
            ])

    def test_get_days(self):
        weeks = self.month.get_weeks()
        week = weeks[0]
        days = week.get_days()
        self.assertEqual(
            [
                (len(day.occurrences), day.start,day.end) for day in days
            ],
            [
                (0, datetime.datetime(2008, 1, 27, 0, 0),
                 datetime.datetime(2008, 1, 28, 0, 0)),
                (0, datetime.datetime(2008, 1, 28, 0, 0),
                 datetime.datetime(2008, 1, 29, 0, 0)),
                (0, datetime.datetime(2008, 1, 29, 0, 0),
                 datetime.datetime(2008, 1, 30, 0, 0)),
                (0, datetime.datetime(2008, 1, 30, 0, 0),
                 datetime.datetime(2008, 1, 31, 0, 0)),
                (0, datetime.datetime(2008, 1, 31, 0, 0),
                 datetime.datetime(2008, 2, 1, 0, 0)),
                (0, datetime.datetime(2008, 2, 1, 0, 0),
                 datetime.datetime(2008, 2, 2, 0, 0)),
                (1, datetime.datetime(2008, 2, 2, 0, 0),
                 datetime.datetime(2008, 2, 3, 0, 0))]
            )




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

    def test_event_creation_annonymous_user(self):
        self.response = c.get(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                              {})
        self.assertEqual(self.response.status_code, 302)

    def test_event_creation_autheticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                              {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post(reverse("s_create_event_in_calendar",
                                      kwargs={"calendar_id":1}),
                               {'description': 'description',
                                'title': 'title',
                                'end_1': '10:22:00','end_0': '2008-10-30',
                                'start_0': '2008-10-30','start_1': '09:21:57'})
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get(reverse("s_event",kwargs={"event_id":2}), {})
        self.assertEqual(self.response.status_code, 200)
        c.logout()

    def test_view_event(self):
        self.response = c.get(reverse("s_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)

    def test_delete_event_annonymous_user(self):
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)

    def test_delete_event_autheticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get(reverse("s_delete_event",kwargs={"event_id":1}), {})
        self.assertEqual(self.response.status_code, 404)
        c.logout()
