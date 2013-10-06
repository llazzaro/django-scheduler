import datetime
import pytz

from django.test import TestCase

from schedule.models import Event, Rule, Calendar
from schedule.models.events import Occurrence
from schedule.periods import Period


class TestOccurrence(TestCase):
    def setUp(self):
        rule = Rule(frequency="WEEKLY")
        rule.save()
        cal = Calendar(name="MyCal")
        cal.save()
        self.recurring_data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': rule,
            'calendar': cal
        }
        self.data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'calendar': cal
        }
        self.recurring_event = Event.objects.create(**self.recurring_data)
        self.start = datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc)
        self.end = datetime.datetime(2008, 1, 27, 0, 0, tzinfo=pytz.utc)

    def test_presisted_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        persisted_occurrence = occurrences[0]
        persisted_occurrence.save()
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        self.assertTrue(occurrences[0].pk)
        self.assertFalse(occurrences[1].pk)

    def test_moved_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        moved_occurrence = occurrences[1]
        span_pre = (moved_occurrence.start, moved_occurrence.end)
        span_post = [x + datetime.timedelta(hours=2) for x in span_pre]
        # check has_occurrence on both periods
        period_pre = Period([self.recurring_event], span_pre[0], span_pre[1])
        period_post = Period([self.recurring_event], span_post[0], span_post[1])
        self.assertTrue(period_pre.has_occurrences())
        self.assertFalse(period_post.has_occurrences())
        # move occurrence
        moved_occurrence.move(moved_occurrence.start + datetime.timedelta(hours=2),
                              moved_occurrence.end + datetime.timedelta(hours=2))
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        self.assertTrue(occurrences[1].moved)
        # check has_occurrence on both periods (the result should be reversed)
        period_pre = Period([self.recurring_event], span_pre[0], span_pre[1])
        period_post = Period([self.recurring_event], span_post[0], span_post[1])
        self.assertFalse(period_pre.has_occurrences())
        self.assertTrue(period_post.has_occurrences())

    def test_cancelled_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        cancelled_occurrence = occurrences[2]
        cancelled_occurrence.cancel()
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        self.assertTrue(occurrences[2].cancelled)
        cancelled_occurrence.uncancel()
        occurrences = self.recurring_event.get_occurrences(start=self.start, end=self.end)
        self.assertFalse(occurrences[2].cancelled)

    def test_occurrence_eq_method(self):
        event2 = Event.objects.create(**self.recurring_data)
        self.assertEqual(self.recurring_event.get_occurrences(start=self.start, end=self.end)[0],
                         event2.get_occurrences(start=self.start, end=self.end)[0])
        self.assertNotEqual(self.recurring_event.get_occurrences(start=self.start, end=self.end)[0],
                            event2.get_occurrences(start=self.start, end=self.end)[1])
        self.assertNotEqual(self.recurring_event.get_occurrences(start=self.start, end=self.end)[0],
                            event2)

    def test_create_occurrence_without_event(self):
        """
        may be required for creating formsets, for example in admin
        """
        o = Occurrence()



