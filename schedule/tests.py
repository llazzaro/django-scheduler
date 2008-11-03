from schedule.forms import GlobalSplitDateTimeWidget
import datetime
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

from django.test import TestCase
from django.test import Client
from django.conf import settings 
c = Client()

class TestUrls(TestCase):
    schedule_fixture = getattr(settings, 'PROJECT_PATH', '/Users/tonyhauber/Projects/django-projects/schedtest/schedule/fixtures/schedule.json')
    
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
