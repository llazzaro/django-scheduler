import datetime
import os

from django.test import TestCase
from django.test import Client
from django.conf import settings

from schedule.forms import GlobalSplitDateTimeWidget
from schedule.models import Event, Rule
from schedule.occurrence import Occurrence

class GlobalSplitDateTimeWidgetTest(object):
    """
    >>> widget = GlobalSplitDateTimeWidget()
    >>> value = datetime.datetime(2008, 1, 1, 5, 5)
    >>> widget.decompress(value)
    [datetime.date(2008, 1, 1), '05:05', 'AM']
    >>> data = {'datetime_0':'2008-1-1', 'datetime_1':'5:05', 'datetime_2': 'PM'}
    >>> widget.value_from_datadict(data, None, 'datetime')
    datetime.datetime(2008, 1, 1, 17, 5)
    >>> widget = GlobalSplitDateTimeWidget(hour24 = True)
    >>> widget.value_from_datadict(data, None, 'datetime')
    ['2008-1-1', '5:05']
    """
    pass

class OccurrenceTest(object):
    """
    >>> rule = Rule(frequency = "WEEKLY")
    >>> data = {
    ...         'title': 'Recent Event',
    ...         'start': datetime.datetime(2008, 1, 5, 8, 0),
    ...         'end': datetime.datetime(2008, 1, 5, 9, 0),
    ...         'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
    ...         'rule': rule,
    ...        }
    >>> recurring_event = Event(**data)
    >>> recurring_event.save()
    >>> occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0),
    ...                             end=datetime.datetime(2008, 1, 20, 0, 0))
    >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
    ['2008-01-12 08:00:00 to 2008-01-12 09:00:00', '2008-01-19 08:00:00 to 2008-01-19 09:00:00']

    """


c = Client()

class TestUrls(TestCase):
    schedule_fixture = os.path.join(getattr(settings, 'PROJECT_DIR'),
                                    "fixtures/schedule.json")

    fixtures = [schedule_fixture]
    def test_calendar_view(self):
        self.response = c.get('/schedule/calendar/1/', {})
        self.assertEqual(self.response.status_code, 200)

    def test_event_creation_annonymous_user(self):
        self.response = c.get('/schedule/calendar/1/create_event/', {})
        self.assertEqual(self.response.status_code, 302)
    def test_event_creation_autheticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get('/schedule/calendar/1/create_event/', {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post('/schedule/calendar/1/create_event/', {'description': 'description','title': 'title','end_1': '10:22:00','end_0': '2008-10-30','start_0': '2008-10-30','start_1': '09:21:57',})
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get('/schedule/event/2/', {})
        self.assertEqual(self.response.status_code, 200)
        c.logout()
    def test_view_event(self):
        self.response = c.get('/schedule/event/1/', {})
        self.assertEqual(self.response.status_code, 200)

    def test_delete_event_annonymous_user(self):
        self.response = c.get('/schedule/event/delete/2/', {})
        self.assertEqual(self.response.status_code, 302)

    def test_delete_event_autheticated_user(self):
        c.login(username="admin", password="admin")
        self.response = c.get('/schedule/event/delete/1/', {})
        self.assertEqual(self.response.status_code, 200)
        self.response = c.post('/schedule/event/delete/1/', {})
        self.assertEqual(self.response.status_code, 302)
        self.response = c.get('/schedule/event/delete/1/', {})
        self.assertEqual(self.response.status_code, 404)
        c.logout()
