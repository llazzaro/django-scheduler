import datetime

from django.test import TestCase

from schedule.forms import EventForm


class TestScheduleForms(TestCase):
    def test_event_form(self):
        now = datetime.datetime.now()
        data = {
            "start_0": now.strftime("%Y-%m-%d"),
            "start_1": "00:00",
            "end_0": (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "end_1": "00:00",
            "title": "some title",
        }
        form = EventForm(data=data)
        validated = form.is_valid()
        self.assertTrue(validated)

        data["end_0"] = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        form = EventForm(data=data)
        validated = form.is_valid()
        self.assertFalse(validated)
        self.assertEqual(len(form.non_field_errors()), 1)
        self.assertEqual(
            form.non_field_errors()[0], "The end time must be later than start time."
        )

        del data["end_0"]
        del data["end_1"]
        del data["start_0"]
        del data["start_1"]
        form = EventForm(data=data)
        validated = form.is_valid()
        self.assertFalse(validated)
        self.assertEqual(len(form.non_field_errors()), 0)
        self.assertEqual(len(form.errors), 2)
        self.assertEqual(len(form.errors["end"]), 1)
        self.assertEqual(form.errors["end"][0], "This field is required.")
        self.assertEqual(len(form.errors["start"]), 1)
        self.assertEqual(form.errors["start"][0], "This field is required.")
