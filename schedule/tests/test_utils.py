import os
import pytz
import datetime

from django.test import TestCase
from django.utils import timezone

from schedule.models import Event, Rule, Calendar
from schedule.utils import EventListManager


class TestEventListManager(TestCase):
    def setUp(self):
        weekly = Rule.objects.create(frequency="WEEKLY")
        daily = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        self.default_tzinfo = timezone.get_default_timezone()

        self.event1 = Event(**{
            'title': 'Weekly Event',
            'start': datetime.datetime(2009, 4, 1, 8, 0, tzinfo=self.default_tzinfo),
            'end': datetime.datetime(2009, 4, 1, 9, 0, tzinfo=self.default_tzinfo),
            'end_recurring_period': datetime.datetime(2009, 10, 5, 0, 0, tzinfo=self.default_tzinfo),
            'rule': weekly,
            'calendar': cal
        })
        self.event1.save()
        self.event2 = Event(**{
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=self.default_tzinfo),
            'end': datetime.datetime(2008, 1, 5, 10, 0, tzinfo=self.default_tzinfo),
            'end_recurring_period': datetime.datetime(2009, 5, 5, 0, 0, tzinfo=self.default_tzinfo),
            'rule': daily,
            'calendar': cal
        })
        self.event2.save()

    def test_occurrences_after(self):
        eml = EventListManager([self.event1, self.event2])
        occurrences = eml.occurrences_after(datetime.datetime(2009, 4, 1, 0, 0, tzinfo=self.default_tzinfo))
        self.assertEqual(next(occurrences).event, self.event1)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event2)
        self.assertEqual(next(occurrences).event, self.event1)
        occurrences = eml.occurrences_after()
        self.assertEqual(list(occurrences), [])
