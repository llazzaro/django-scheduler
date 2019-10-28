import datetime

from django.test import TestCase
from django.utils import timezone

from schedule.models import Calendar, Event, Occurrence, Rule
from schedule.utils import EventListManager, OccurrenceReplacer


class TestEventListManager(TestCase):
    def setUp(self):
        weekly = Rule.objects.create(frequency="WEEKLY")
        daily = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        self.default_tzinfo = timezone.get_default_timezone()

        self.event1 = Event.objects.create(
            title="Weekly Event",
            start=datetime.datetime(2009, 4, 1, 8, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2009, 4, 1, 9, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(
                2009, 10, 5, 0, 0, tzinfo=self.default_tzinfo
            ),
            rule=weekly,
            calendar=cal,
        )
        self.event2 = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2008, 1, 5, 10, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(
                2009, 5, 5, 0, 0, tzinfo=self.default_tzinfo
            ),
            rule=daily,
            calendar=cal,
        )

    def test_occurrences_after(self):
        eml = EventListManager([self.event1, self.event2])
        occurrences = eml.occurrences_after(
            datetime.datetime(2009, 4, 1, 0, 0, tzinfo=self.default_tzinfo)
        )
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


class TestOccurrenceReplacer(TestCase):
    def setUp(self):
        weekly = Rule.objects.create(frequency="WEEKLY")
        daily = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        self.default_tzinfo = timezone.get_default_timezone()
        self.start = timezone.now() - datetime.timedelta(days=10)
        self.end = self.start + datetime.timedelta(days=300)
        self.event1 = Event.objects.create(
            title="Weekly Event",
            start=self.start,
            end=self.end,
            end_recurring_period=self.end,
            rule=weekly,
            calendar=cal,
        )
        self.occ = Occurrence.objects.create(
            event=self.event1,
            start=self.start,
            end=self.end,
            original_start=self.start,
            original_end=self.end,
        )

        self.event2 = Event.objects.create(
            title="Recent Event",
            start=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2008, 1, 5, 10, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(
                2009, 5, 5, 0, 0, tzinfo=self.default_tzinfo
            ),
            rule=daily,
            calendar=cal,
        )

    def test_has_occurrence(self):
        other_occ = Occurrence.objects.create(
            event=self.event1,
            start=self.start,
            end=self.end,
            original_start=self.start,
            original_end=self.end,
        )
        occ_replacer = OccurrenceReplacer([self.occ])

        self.assertTrue(occ_replacer.has_occurrence(self.occ))
        self.assertTrue(occ_replacer.has_occurrence(other_occ))

    def test_has_occurrence_with_other_event(self):
        other_occ = Occurrence.objects.create(
            event=self.event2,
            start=self.start,
            end=self.end,
            original_start=self.start,
            original_end=self.end,
        )
        occ_replacer = OccurrenceReplacer([self.occ])

        self.assertTrue(occ_replacer.has_occurrence(self.occ))
        self.assertFalse(occ_replacer.has_occurrence(other_occ))

    def test_get_additional_occurrences(self):
        occ_replacer = OccurrenceReplacer([self.occ])
        # Other occurrence.
        Occurrence.objects.create(
            event=self.event2,
            start=self.start + datetime.timedelta(days=5),
            end=self.end,
            original_start=self.start,
            original_end=self.end,
        )
        res = occ_replacer.get_additional_occurrences(self.start, self.end)
        self.assertEqual(res, [self.occ])

    def test_get_additional_occurrences_cancelled(self):
        occ_replacer = OccurrenceReplacer([self.occ])
        self.occ.cancelled = True
        self.occ.save()
        res = occ_replacer.get_additional_occurrences(self.start, self.end)
        self.assertEqual(res, [])

    def test_get_occurrence(self):
        # self.occ is a persisted Occurrence
        occ_replacer = OccurrenceReplacer([self.occ])
        res = occ_replacer.get_occurrence(self.occ)
        self.assertEqual(res, self.occ)
        res = occ_replacer.get_occurrence(self.occ)
        self.assertEqual(res, self.occ)

    def test_get_occurrence_works_for_event_like_object(self):
        # get_occurrence method checks the duck
        occ_replacer = OccurrenceReplacer([self.occ])
        with self.assertRaises(AttributeError):
            occ_replacer.get_occurrence(int)
