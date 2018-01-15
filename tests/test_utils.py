import datetime
from contextlib import contextmanager

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils import timezone

from schedule import utils
from schedule.models import Calendar, Event, Occurrence, Rule


class TestEventListManager(TestCase):
    def setUp(self):
        weekly = Rule.objects.create(frequency="WEEKLY")
        daily = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        self.default_tzinfo = timezone.get_default_timezone()

        self.event1 = Event.objects.create(
            title='Weekly Event',
            start=datetime.datetime(2009, 4, 1, 8, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2009, 4, 1, 9, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(2009, 10, 5, 0, 0, tzinfo=self.default_tzinfo),
            rule=weekly,
            calendar=cal,
        )
        self.event2 = Event.objects.create(
            title='Recent Event',
            start=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2008, 1, 5, 10, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(2009, 5, 5, 0, 0, tzinfo=self.default_tzinfo),
            rule=daily,
            calendar=cal,
        )

    def test_occurrences_after(self):
        eml = utils.EventListManager([self.event1, self.event2])
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


class TestOccurrenceReplacer(TestCase):

    def setUp(self):
        weekly = Rule.objects.create(frequency="WEEKLY")
        daily = Rule.objects.create(frequency="DAILY")
        cal = Calendar.objects.create(name="MyCal")
        self.default_tzinfo = timezone.get_default_timezone()
        self.start = timezone.now() - datetime.timedelta(days=10)
        self.end = self.start + datetime.timedelta(days=300)
        self.event1 = Event.objects.create(
            title='Weekly Event',
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
            original_end=self.end)

        self.event2 = Event.objects.create(
            title='Recent Event',
            start=datetime.datetime(2008, 1, 5, 9, 0, tzinfo=self.default_tzinfo),
            end=datetime.datetime(2008, 1, 5, 10, 0, tzinfo=self.default_tzinfo),
            end_recurring_period=datetime.datetime(2009, 5, 5, 0, 0, tzinfo=self.default_tzinfo),
            rule=daily,
            calendar=cal,
        )

    def test_has_occurrence(self):
        other_occ = Occurrence.objects.create(
            event=self.event1,
            start=self.start,
            end=self.end,
            original_start=self.start,
            original_end=self.end)
        occ_replacer = utils.OccurrenceReplacer([self.occ])

        self.assertTrue(occ_replacer.has_occurrence(self.occ))
        self.assertTrue(occ_replacer.has_occurrence(other_occ))

    def test_has_occurrence_with_other_event(self):
        other_occ = Occurrence.objects.create(
            event=self.event2,
            start=self.start,
            end=self.end,
            original_start=self.start,
            original_end=self.end)
        occ_replacer = utils.OccurrenceReplacer([self.occ])

        self.assertTrue(occ_replacer.has_occurrence(self.occ))
        self.assertFalse(occ_replacer.has_occurrence(other_occ))

    def test_get_additional_occurrences(self):
        occ_replacer = utils.OccurrenceReplacer([self.occ])
        # Other occurrence.
        Occurrence.objects.create(
            event=self.event2,
            start=self.start + datetime.timedelta(days=5),
            end=self.end,
            original_start=self.start,
            original_end=self.end)
        res = occ_replacer.get_additional_occurrences(self.start, self.end)
        self.assertEqual(res, [self.occ])

    def test_get_additional_occurrences_cancelled(self):
        occ_replacer = utils.OccurrenceReplacer([self.occ])
        self.occ.cancelled = True
        self.occ.save()
        res = occ_replacer.get_additional_occurrences(self.start, self.end)
        self.assertEqual(res, [])

    def test_get_occurrence(self):
        # self.occ is a persisted Occurrence
        occ_replacer = utils.OccurrenceReplacer([self.occ])
        res = occ_replacer.get_occurrence(self.occ)
        self.assertEqual(res, self.occ)
        res = occ_replacer.get_occurrence(self.occ)
        self.assertEqual(res, self.occ)

    def test_get_occurrence_works_for_event_like_object(self):
        # get_occurrence method checks the duck
        occ_replacer = utils.OccurrenceReplacer([self.occ])
        with self.assertRaises(AttributeError):
            occ_replacer.get_occurrence(int)


@contextmanager
def override_local_settings(**kwargs):
    previous = {}
    for key in kwargs:
        previous[key] = getattr(utils, key)
        setattr(utils, key, kwargs[key])
    try:
        yield
    finally:
        for key in previous:
            setattr(utils, key, previous[key])


class TestUtils(TestCase):

    def test_get_calendar_model(self):
        model = utils.get_calendar_model()
        self.assertIs(model, Calendar)

    def test_get_calendar_model_swapped_bad_settings(self):
        with override_local_settings(SCHEDULER_CALENDAR_MODEL='badsetting'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_CALENDAR_MODEL must be of the form 'app_label.model_name'"):
                utils.get_calendar_model()

    def test_get_calendar_model_swapped_unknown_model(self):
        with override_local_settings(SCHEDULER_CALENDAR_MODEL='stuff.Model'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_CALENDAR_MODEL refers to model 'stuff.Model' that has not been installed"):
                utils.get_calendar_model()

    def test_get_event_model(self):
        model = utils.get_event_model()
        self.assertIs(model, Event)

    def test_get_event_model_swapped_bad_settings(self):
        with override_local_settings(SCHEDULER_EVENT_MODEL='badsetting'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_EVENT_MODEL must be of the form 'app_label.model_name'"):
                utils.get_event_model()

    def test_get_event_model_swapped_unknown_model(self):
        with override_local_settings(SCHEDULER_EVENT_MODEL='stuff.Model'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_EVENT_MODEL refers to model 'stuff.Model' that has not been installed"):
                utils.get_event_model()

    def test_get_occurrence_model(self):
        model = utils.get_occurrence_model()
        self.assertIs(model, Occurrence)

    def test_test_get_occurrence_model_swapped_bad_settings(self):
        with override_local_settings(SCHEDULER_OCCURRENCE_MODEL='badsetting'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_OCCURRENCE_MODEL must be of the form 'app_label.model_name'"):
                utils.get_occurrence_model()

    def test_test_get_occurrence_model_swapped_unknown_model(self):
        with override_local_settings(SCHEDULER_OCCURRENCE_MODEL='stuff.Model'):
            with self.assertRaisesMessage(ImproperlyConfigured, "SCHEDULER_OCCURRENCE_MODEL refers to model 'stuff.Model' that has not been installed"):
                utils.get_occurrence_model()
