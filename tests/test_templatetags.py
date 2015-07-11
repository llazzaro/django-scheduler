import datetime
import pytz

from django.test import TestCase
from django.utils.html import escape
from schedule.models import Event, Rule, Calendar
from schedule.periods import Period, Day

from schedule.templatetags.scheduletags import querystring_for_date, prev_url, next_url, create_event_url


class TestTemplateTags(TestCase):
    def setUp(self):
        self.day = Day(events=Event.objects.all(),
                       date=datetime.datetime(datetime.datetime.now().year, 2, 7, 0, 0, tzinfo=pytz.utc))
        self.day_out_of_limit = Day(events=Event.objects.all(),
                       date=datetime.datetime(datetime.datetime.now().year + 3, 2, 7, 0, 0, tzinfo=pytz.utc))
        self.day_out_of_limit_lower = Day(events=Event.objects.all(),
                       date=datetime.datetime(datetime.datetime.now().year - 3, 2, 7, 0, 0, tzinfo=pytz.utc))

        rule = Rule(frequency='WEEKLY')
        rule.save()
        self.cal = Calendar(name='MyCal', slug='MyCalSlug')
        self.cal.save()

        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(datetime.datetime.now().year, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(datetime.datetime.now().year, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(datetime.datetime.now().year, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': rule,
            'calendar': self.cal,
        }
        recurring_event = Event(**data)
        recurring_event.save()
        self.period = Period(events=Event.objects.all(),
                             start=datetime.datetime(datetime.datetime.now().year, 1, 4, 7, 0, tzinfo=pytz.utc),
                             end=datetime.datetime(datetime.datetime.now().year, 1, 21, 7, 0, tzinfo=pytz.utc))

    def test_querystring_for_datetime(self):
        date = datetime.datetime(datetime.datetime.now().year, 1, 1, 0, 0, 0)
        query_string = querystring_for_date(date, autoescape=True)
        self.assertEqual(escape('?year={0}&month=1&day=1&hour=0&minute=0&second=0'.format(datetime.datetime.now().year)),
            query_string)

    def test_prev_url(self):
        query_string = prev_url('month_calendar', self.cal, self.day)
        url_params = escape('/calendar/month/MyCalSlug/?year={0}&month=2&day=6&hour=0&minute=0&second=0'.format(datetime.datetime.now().year))
        expected = ('<a href="{0}"><span class="glyphicon glyphicon-circle-arrow-left" /></a>'.format(url_params))
        self.assertEqual(query_string, expected)

    def test_next_url(self):
        query_string = next_url('month_calendar', self.cal, self.day)
        url_params = escape('/calendar/month/MyCalSlug/?year={0}&month=2&day=8&hour=0&minute=0&second=0'.format(datetime.datetime.now().year))
        expected = ('<a href="{0}"><span class="glyphicon glyphicon-circle-arrow-right" /></a>'.format(url_params))
        self.assertEqual(query_string, expected)

    def test_next_url_upper_limit(self):
        query_string = next_url('month_calendar', self.cal, self.day_out_of_limit)
        self.assertEqual(query_string, '')

    def test_prev_url_lower_limit(self):
        query_string = prev_url('month_calendar', self.cal, self.day_out_of_limit_lower)
        self.assertEqual(query_string, '')

    def test_create_event_url(self):
        context = {}
        slot = self.period.get_time_slot(datetime.datetime(datetime.datetime.now().year, 1, 4, 7, 0, tzinfo=pytz.utc),
                                         datetime.datetime(datetime.datetime.now().year, 1, 4, 7, 12, tzinfo=pytz.utc))
        query_string = create_event_url(context, self.cal, slot.start)
        expected = ('/event/create/MyCalSlug/?year={0}&month=1&day=4&hour=7&minute=0&second=0'.format(datetime.datetime.now().year))
        self.assertEqual(query_string['create_event_url'], escape(expected))
