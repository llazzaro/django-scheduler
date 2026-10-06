import datetime
from unittest.mock import patch

import pytz
from django.test import SimpleTestCase

from schedule.models import Event, Rule


class TestRecurrenceConstruction(SimpleTestCase):
    def setUp(self):
        self.start = datetime.datetime(2024, 1, 1, 8, tzinfo=pytz.UTC)
        self.event = Event(
            start=self.start,
            end=self.start + datetime.timedelta(hours=1),
            rule=Rule(frequency="DAILY"),
            end_recurring_period=self.start + datetime.timedelta(days=3),
        )

    def test_rule_builder_respects_event_parameter_overrides(self):
        with patch.object(
            self.event, "_event_params", return_value={"interval": 2}
        ) as params:
            rule = self.event.get_rrule_object(pytz.UTC)
        params.assert_called_once_with()
        self.assertEqual(
            list(rule),
            [datetime.datetime(2024, 1, 1, 8), datetime.datetime(2024, 1, 3, 8)],
        )

    def test_parameter_selection_keeps_rule_input_unchanged(self):
        params = {"byhour": [8, 9], "interval": 2}
        with patch.object(self.event.rule, "get_params", return_value=params):
            selected = self.event._event_params()
        self.assertEqual(selected, {"byhour": [8], "interval": 2})
        self.assertEqual(params, {"byhour": [8, 9], "interval": 2})

    def test_rule_builder_converts_aware_bounds_to_query_wall_time(self):
        rule = self.event.get_rrule_object(pytz.timezone("America/Chicago"))
        self.assertEqual(next(iter(rule)), datetime.datetime(2024, 1, 1, 2))
        self.assertEqual(list(rule)[-1], datetime.datetime(2024, 1, 4, 2))

    def test_one_time_event_has_no_recurrence_rule(self):
        self.event.rule = None
        self.assertIsNone(self.event.get_rrule_object(pytz.UTC))
