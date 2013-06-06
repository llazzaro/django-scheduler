import datetime
import pytz

from django.test import TestCase

from schedule.models import Event, Rule, Calendar
from schedule.periods import Period, Day

class TestEvent(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        cal = Calendar(name="MyCal")
        cal.save()
        self.recurring_data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                'rule': rule,
                'calendar': cal
               }
        self.data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                'end': datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                'calendar': cal
               }

    def test_edge_case_events(self):
        cal = Calendar(name="MyCal")
        cal.save()
        data_1 = {
                'title': 'Edge case event test one',
                'start': datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
                'end': datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                'calendar': cal
               }
        data_2 = {
                'title': 'Edge case event test two',
                'start': datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                'end': datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
                'calendar': cal
               }
        event_one = Event(**data_1)
        event_two = Event(**data_2)
        event_one.save()
        event_two.save()
        occurrences_two = event_two.get_occurrences( datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc), datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))
        self.assertEquals(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences( datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc), datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))
        self.assertEquals(0, len(occurrences_one))

    def test_recurring_event_get_occurrences(self):
        recurring_event = Event(**self.recurring_data)
        occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
                                    end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(["%s to %s" %(o.start, o.end) for o in occurrences],
                ['2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00', '2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00'])

    def test_event_get_occurrences_after(self):
        recurring_event=Event(**self.recurring_data)
        recurring_event.save()
        #occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 5, tzinfo=pytz.utc),
        #    end = datetime.datetime(2008, 1, 6, tzinfo=pytz.utc))
        #occurrence = occurrences[0]
        #occurrence2 = recurring_event.occurrences_after(datetime.datetime(2008, 1, 5, tzinfo=pytz.utc)).next()
        #self.assertEqual(occurrence, occurrence2)

    def test_get_occurrence(self):
        event = Event(**self.recurring_data)
        event.save()
        occurrence = event.get_occurrence(datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc))
        self.assertEqual(occurrence.start, datetime.datetime(2008, 1, 5, 8, tzinfo=pytz.utc))
        occurrence.save()
        occurrence = event.get_occurrence(datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc))
        self.assertTrue(occurrence.pk is not None)

    def test_prevent_type_error_when_comparing_naive_and_aware_dates(self):
        # this only test if the TypeError is raised
        event = Event(**self.recurring_data)
        event.save()
        naive_date = datetime.datetime(2008, 1, 20, 0, 0)
        self.assertIsNone(event.get_occurrence(naive_date))
