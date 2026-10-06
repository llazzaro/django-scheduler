import datetime
from unittest.mock import Mock, patch

import pytz
from django.test import SimpleTestCase

from schedule.models import Occurrence
from schedule.periods import Period


class TestPeriodOccurrenceCallbacks(SimpleTestCase):
    def setUp(self):
        start = datetime.datetime(2024, 1, 1, tzinfo=pytz.UTC)
        self.period = Period([], start, start + datetime.timedelta(days=1))
        self.occurrence = Occurrence(
            start=start, end=start + datetime.timedelta(hours=1)
        )

    def test_cached_occurrences_use_period_retrieval_override_once(self):
        occurrences = [self.occurrence]
        with patch.object(
            self.period, "_get_sorted_occurrences", return_value=occurrences
        ) as retrieve:
            self.assertIs(self.period.occurrences, occurrences)
            self.assertIs(self.period.get_occurrences(), occurrences)
        retrieve.assert_called_once_with()

    def test_partials_and_visibility_respect_classification_overrides(self):
        self.period.occurrence_pool = [self.occurrence]
        classified = {"occurrence": self.occurrence, "class": 3}
        with patch.object(
            self.period, "classify_occurrence", return_value=classified
        ) as classify:
            self.assertEqual(self.period.get_occurrence_partials(), [classified])
            self.assertTrue(self.period.has_occurrences())
        self.assertEqual(classify.call_count, 2)
        classify.assert_called_with(self.occurrence)

    def test_parent_persisted_occurrences_are_reused_without_queries(self):
        persisted = [self.occurrence]
        self.period._persisted_occurrences = persisted
        self.assertIs(self.period.get_persisted_occurrences(), persisted)

    def test_empty_persisted_queryset_is_cached(self):
        persisted = []
        model = Mock()
        model.objects.filter.return_value = persisted
        with patch("schedule.periods.Occurrence", model):
            self.assertIs(self.period.get_persisted_occurrences(), persisted)
            self.assertIs(self.period.get_persisted_occurrences(), persisted)
        model.objects.filter.assert_called_once_with(event__in=self.period.events)
