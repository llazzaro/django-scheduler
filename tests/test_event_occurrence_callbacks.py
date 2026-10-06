import datetime
from unittest.mock import patch

import pytz
from django.test import TestCase

from schedule.models import Calendar, Event, Rule


class TestEventOccurrenceCallbacks(TestCase):
    def setUp(self):
        self.start = datetime.datetime(2024, 1, 1, 8, tzinfo=pytz.UTC)
        self.event = Event.objects.create(
            start=self.start,
            end=self.start + datetime.timedelta(hours=1),
            rule=Rule.objects.create(frequency="DAILY"),
            calendar=Calendar.objects.create(name="Callbacks"),
            end_recurring_period=self.start + datetime.timedelta(days=3),
        )

    def test_window_generation_respects_occurrence_factory_override(self):
        occurrence = self.event._create_occurrence(self.start)
        with patch.object(
            self.event, "_create_occurrence", return_value=occurrence
        ) as create:
            occurrences = self.event._get_occurrence_list(
                self.start, self.start + datetime.timedelta(days=2)
            )
        self.assertEqual(occurrences, [occurrence])
        self.assertEqual(create.call_count, 2)
        create.assert_called_with(
            self.start + datetime.timedelta(days=1),
            self.event.end + datetime.timedelta(days=1),
        )

    def test_persisted_replacement_respects_window_generation_override(self):
        occurrence = self.event._create_occurrence(self.start)
        occurrence.save()
        generated = self.event._create_occurrence(self.start)
        with patch.object(
            self.event, "_get_occurrence_list", return_value=[generated]
        ) as generate:
            occurrences = self.event.get_occurrences(self.start, self.event.end)
        generate.assert_called_once_with(self.start, self.event.end)
        self.assertEqual([item.pk for item in occurrences], [occurrence.pk])

    def test_streaming_respects_generator_override(self):
        occurrence = self.event._create_occurrence(self.start)
        with patch.object(
            self.event, "_occurrences_after_generator", return_value=iter([occurrence])
        ) as generate:
            occurrences = list(
                self.event.occurrences_after(self.start, max_occurrences=1)
            )
        generate.assert_called_once_with(self.start)
        self.assertEqual(occurrences, [occurrence])

    def test_lookup_respects_rule_and_factory_overrides(self):
        occurrence = self.event._create_occurrence(self.start)
        with (
            patch.object(self.event, "get_rrule_object", return_value=None) as rule,
            patch.object(
                self.event, "_create_occurrence", return_value=occurrence
            ) as create,
        ):
            self.assertIs(self.event.get_occurrence(self.start), occurrence)
        rule.assert_called_once_with(pytz.UTC)
        create.assert_called_once_with(self.start)
