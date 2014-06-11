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
                       date=datetime.datetime(2008, 2, 7, 0, 0, tzinfo=pytz.utc))
        rule = Rule(frequency="WEEKLY")
        rule.save()
        self.cal = Calendar(name="MyCal", slug="MyCalSlug")
        self.cal.save()
        data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': rule,
            'calendar': self.cal,
        }
        recurring_event = Event(**data)
        recurring_event.save()
        self.period = Period(events=Event.objects.all(),
                             start=datetime.datetime(2008, 1, 4, 7, 0, tzinfo=pytz.utc),
                             end=datetime.datetime(2008, 1, 21, 7, 0, tzinfo=pytz.utc))

    def test_querystring_for_datetime(self):
        date = datetime.datetime(2008, 1, 1, 0, 0, 0)
        query_string = querystring_for_date(date, autoescape=True)
        self.assertEqual(escape("?year=2008&month=1&day=1&hour=0&minute=0&second=0"),
            query_string)

    def test_prev_url(self):
        query_string = prev_url("month_calendar", 'MyCalSlug', self.day)
        expected = ("/calendar/month/MyCalSlug/?year=2008&month=2&day=6&hour=0"
                    "&minute=0&second=0")
        self.assertEqual(query_string, escape(expected))

    def test_next_url(self):
        query_string = next_url("month_calendar", 'MyCalSlug', self.day)
        expected = ("/calendar/month/MyCalSlug/?year=2008&month=2&day=8&hour=0"
                    "&minute=0&second=0")
        self.assertEqual(query_string, escape(expected))

    def test_create_event_url(self):
        context = {}
        slot = self.period.get_time_slot(datetime.datetime(2010, 1, 4, 7, 0, tzinfo=pytz.utc),
                                         datetime.datetime(2008, 1, 4, 7, 12, tzinfo=pytz.utc))
        query_string = create_event_url(context, self.cal, slot.start)
        expected = ("/event/create/MyCalSlug/?year=2010&month=1&day=4&hour=7"
                    "&minute=0&second=0")
        self.assertEqual(query_string['create_event_url'], escape(expected))

