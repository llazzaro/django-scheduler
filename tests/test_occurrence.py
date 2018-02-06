import datetime

import pytz
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from schedule.models import Calendar, Event, Rule
from schedule.models.events import Occurrence
from schedule.periods import Period


class TestOccurrence(TestCase):
    def setUp(self):
        rule = Rule.objects.create(frequency="WEEKLY")
        cal = Calendar.objects.create(name="MyCal")
        self.recurring_data = {
            'title': 'Recent Event',
            'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
            'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
            'end_recurring_period': datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
            'rule': rule,
            'calendar': cal
        }
        self.recurring_event = Event.objects.create(**self.recurring_data)
        self.start = datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc)
        self.end = datetime.datetime(2008, 1, 27, 0, 0, tzinfo=pytz.utc)

    @override_settings(TIME_ZONE='America/Toronto')
    def test_persisted_occurrences_with_modified_start_time(self):
        tzinfo = timezone.get_default_timezone()
        # Create a recurring event with a non-UTC timezone
        recurring_event = {
            'title': 'Recurring Event in localtime',
            'start': tzinfo.localize(datetime.datetime(2008, 1, 5, 8, 0)),
            'end': tzinfo.localize(datetime.datetime(2008, 1, 5, 9, 0)),
            'end_recurring_period': tzinfo.localize(datetime.datetime(2008, 1, 10, 0, 0)),
            'rule': Rule.objects.create(frequency="DAILY"),
            'calendar': Calendar.objects.create(name="MyCal")
        }
        r_event = Event.objects.create(**recurring_event)
        # Create a persistent occurrence, with a modified start/end date
        data = {
            'event_id': r_event.id,
            'title': 'Saved Occurrence',
            'start': tzinfo.localize(datetime.datetime(2008, 1, 7, 9, 0)),
            'end': tzinfo.localize(datetime.datetime(2008, 1, 7, 10, 0)),
            'original_start': tzinfo.localize(datetime.datetime(2008, 1, 7, 8, 0)),
            'original_end': tzinfo.localize(datetime.datetime(2008, 1, 7, 9, 0)),
        }
        p_occ = Occurrence.objects.create(**data)
        period_start = tzinfo.localize(datetime.datetime(2008, 1, 7, 0, 0))
        period_end = tzinfo.localize(datetime.datetime(2008, 1, 8, 0, 0))
        occurrences = r_event.get_occurrences(start=period_start, end=period_end)
        occ_start = occurrences[0].start
        self.assertEqual(occ_start.tzinfo, period_start.tzinfo)
        self.assertEqual(p_occ.original_start + datetime.timedelta(hours=1), occ_start)

    def test_persisted_occurrences(self):
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
        Occurrence()

    def test_get_occurrences_non_intersection_returns_empty_occ(self):
        rule = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal", slug='mycal')
        recurring_event = Event.objects.create(
            title='Recent Event',
            start=datetime.datetime(2016, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2016, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2016, 8, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )
        occurrences = recurring_event.get_occurrences(start=self.start, end=self.end)
        self.assertEqual(occurrences, [])

    def test_get_occurrences_is_sorted(self):
        rule = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal", slug='mycal')
        recurring_event = Event.objects.create(
            title='Recent Event',
            start=datetime.datetime(2016, 1, 5, 8, 0, tzinfo=pytz.utc),
            end=datetime.datetime(2016, 1, 5, 9, 0, tzinfo=pytz.utc),
            end_recurring_period=datetime.datetime(2016, 8, 5, 0, 0, tzinfo=pytz.utc),
            rule=rule,
            calendar=cal,
        )

        start = datetime.datetime(2016, 1, 12, 0, 0, tzinfo=pytz.utc)
        end = datetime.datetime(2016, 1, 27, 0, 0, tzinfo=pytz.utc)
        occurrences = recurring_event.get_occurrences(start=start, end=end)

        sorted_occurrences = sorted(occurrences, key=lambda occ: occ.start)

        self.assertEqual(occurrences, sorted_occurrences)
