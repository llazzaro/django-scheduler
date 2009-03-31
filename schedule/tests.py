import datetime
import os

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from schedule.forms import GlobalSplitDateTimeWidget
from schedule.models import Event, Rule, Occurrence
from schedule.periods import Period, Month, Day
from schedule.utils import EventListManager


class TestSplitDateTimeWidget(TestCase):
    def setUp(self):
        self.widget = GlobalSplitDateTimeWidget()
        self.value = datetime.datetime(2008, 1, 1, 5, 5)
        self.data = {'datetime_0':'2008-1-1', 'datetime_1':'5:05', 'datetime_2': 'PM'}
    def test_widget_decompress(self):
        self.assertEquals(self.widget.decompress(self.value),
                          [datetime.date(2008, 1, 1), '05:05', 'AM'])

    def test_widget_value_from_datadict(self):
        self.assertEquals(self.widget.value_from_datadict(self.data, None, 'datetime'),
                          datetime.datetime(2008, 1, 1, 17, 5))
        widget = GlobalSplitDateTimeWidget(hour24 = True)
        self.assertEquals(widget.value_from_datadict(self.data, None, 'datetime'),
                          ['2008-1-1', '5:05'])

class TestEvent(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        self.recurring_data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        self.data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
               }
        
        
    def test_recurring_event_get_occurrences(self):
        recurring_event = Event(**self.recurring_data)
        occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0),
                                    end=datetime.datetime(2008, 1, 20, 0, 0))
        self.assertEquals(["%s to %s" %(o.start, o.end) for o in occurrences],
            ['2008-01-12 08:00:00 to 2008-01-12 09:00:00', '2008-01-19 08:00:00 to 2008-01-19 09:00:00'])


class TestOccurrence(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        self.recurring_data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        self.data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
               }
        self.recurring_event = Event(**self.recurring_data)
        self.recurring_event.save()
        self.start = datetime.datetime(2008, 1, 12, 0, 0)
        self.end = datetime.datetime(2008, 1, 27, 0, 0)
    
    def test_presisted_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        persisted_occurrence = occurrences[0]
        persisted_occurrence.save()
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        self.assertTrue(occurrences[0].pk)
        self.assertFalse(occurrences[1].pk)
    
    def test_moved_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        moved_occurrence = occurrences[1]
        moved_occurrence.move(moved_occurrence.start+datetime.timedelta(hours=2),
                              moved_occurrence.end+datetime.timedelta(hours=2))
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        self.assertTrue(occurrences[1].moved)
    
    def test_cancelled_occurrences(self):
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        cancelled_occurrence = occurrences[2]
        cancelled_occurrence.cancel()
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        self.assertTrue(occurrences[2].cancelled)
        cancelled_occurrence.uncancel()
        occurrences = self.recurring_event.get_occurrences(start=self.start,
                                    end=self.end)
        self.assertFalse(occurrences[2].cancelled)
        

class TestPeriod(TestCase):

    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        recurring_event = Event(**data)
        recurring_event.save()
        self.period = Period(events=Event.objects.all(),
                            start = datetime.datetime(2008,1,4,7,0),
                            end = datetime.datetime(2008,1,21,7,0))
    def test_get_occurrences(self):
        occurrence_list = self.period.occurrences
        self.assertEqual(["%s to %s" %(o.start, o.end) for o in occurrence_list],
            ['2008-01-05 08:00:00 to 2008-01-05 09:00:00',
             '2008-01-12 08:00:00 to 2008-01-12 09:00:00',
             '2008-01-19 08:00:00 to 2008-01-19 09:00:00'])

    def test_get_occurrence_partials(self):
        occurrence_dicts = self.period.get_occurrence_partials()
        self.assertEqual(
            [(occ_dict["class"],
            occ_dict["occurrence"].start,
            occ_dict["occurrence"].end)
            for occ_dict in occurrence_dicts],
            [
                (1,
                 datetime.datetime(2008, 1, 5, 8, 0),
                 datetime.datetime(2008, 1, 5, 9, 0)),
                (1,
                 datetime.datetime(2008, 1, 12, 8, 0),
                 datetime.datetime(2008, 1, 12, 9, 0)),
                (1,
                 datetime.datetime(2008, 1, 19, 8, 0),
                 datetime.datetime(2008, 1, 19, 9, 0))
            ])

    def test_has_occurrence(self):
        self.assert_( self.period.has_occurrences() )
        slot = self.period.get_time_slot( datetime.datetime(2008,1,4,7,0),
                                          datetime.datetime(2008,1,4,7,12) )
        self.failIf( slot.has_occurrences() )

class TestMonth(TestCase):
    def setUp(self):
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        data = {
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 8, 0),
                'end': datetime.datetime(2008, 1, 5, 9, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': rule,
               }
        recurring_event = Event(**data)
        recurring_event.save()
        self.month = Month(events=Event.objects.all(),
                           date=datetime.datetime(2008, 2, 7, 9, 0))
    def test_get_weeks(self):
        weeks = self.month.get_weeks()
        self.assertEqual([(week.start,week.end) for week in weeks],
            [
                (datetime.datetime(2008, 1, 27, 0, 0),
                datetime.datetime(2008, 2, 3, 0, 0)),
                (datetime.datetime(2008, 2, 3, 0, 0),
                datetime.datetime(2008, 2, 10, 0, 0)),
                (datetime.datetime(2008, 2, 10, 0, 0),
                 datetime.datetime(2008, 2, 17, 0, 0)),
                (datetime.datetime(2008, 2, 17, 0, 0),
                 datetime.datetime(2008, 2, 24, 0, 0)),
                (datetime.datetime(2008, 2, 24, 0, 0),
                 datetime.datetime(2008, 3, 2, 0, 0))
            ])

    def test_get_days(self):
        weeks = self.month.get_weeks()
        week = weeks[0]
        days = week.get_days()
        self.assertEqual(
            [
                (len(day.occurrences), day.start,day.end) for day in days
            ],
            [
                (0, datetime.datetime(2008, 1, 27, 0, 0),
                 datetime.datetime(2008, 1, 28, 0, 0)),
                (0, datetime.datetime(2008, 1, 28, 0, 0),
                 datetime.datetime(2008, 1, 29, 0, 0)),
                (0, datetime.datetime(2008, 1, 29, 0, 0),
                 datetime.datetime(2008, 1, 30, 0, 0)),
                (0, datetime.datetime(2008, 1, 30, 0, 0),
                 datetime.datetime(2008, 1, 31, 0, 0)),
                (0, datetime.datetime(2008, 1, 31, 0, 0),
                 datetime.datetime(2008, 2, 1, 0, 0)),
                (0, datetime.datetime(2008, 2, 1, 0, 0),
                 datetime.datetime(2008, 2, 2, 0, 0)),
                (1, datetime.datetime(2008, 2, 2, 0, 0),
                 datetime.datetime(2008, 2, 3, 0, 0))]
            )

    def test_month_convenience_functions(self):
        self.assertEqual( self.month.prev_month(), datetime.datetime(2008, 1, 1, 0, 0))
        self.assertEqual( self.month.next_month(), datetime.datetime(2008, 3, 1, 0, 0))
        self.assertEqual( self.month.current_year(), datetime.datetime(2008, 1, 1, 0, 0))
        self.assertEqual( self.month.prev_year(), datetime.datetime(2007, 1, 1, 0, 0))
        self.assertEqual( self.month.next_year(), datetime.datetime(2009, 1, 1, 0, 0))

class TestDay(TestCase):
    def setUp(self):
        self.day = Day(events=Event.objects.all(),
                           date=datetime.datetime(2008, 2, 7, 9, 0))

    def test_day_setup(self):
        self.assertEqual( self.day.start, datetime.datetime(2008, 2, 7, 0, 0))
        self.assertEqual( self.day.end, datetime.datetime(2008, 2, 8, 0, 0))

    def test_day_convenience_functions(self):
        self.assertEqual( self.day.prev_day(), datetime.datetime(2008, 2, 6, 0, 0))
        self.assertEqual( self.day.next_day(), datetime.datetime(2008, 2, 8, 0, 0))

    def test_time_slot(self):
        slot_start = datetime.datetime(2008, 2, 7, 13, 30)
        slot_end = datetime.datetime(2008, 2, 7, 15, 0)
        period = self.day.get_time_slot( slot_start, slot_end )
        self.assertEqual( period.start, slot_start )
        self.assertEqual( period.end, slot_end )

class TestEventListManager(TestCase):
    def setUp(self):
        weekly = Rule(frequency = "WEEKLY")
        weekly.save()
        daily = Rule(frequency = "DAILY")
        daily.save()
        
        self.event1 = Event(**{
                'title': 'Weekly Event',
                'start': datetime.datetime(2009, 4, 1, 8, 0),
                'end': datetime.datetime(2009, 4, 1, 9, 0),
                'end_recurring_period' : datetime.datetime(2009, 10, 5, 0, 0),
                'rule': weekly,
               })
        self.event1.save()
        self.event2 = Event(**{
                'title': 'Recent Event',
                'start': datetime.datetime(2008, 1, 5, 9, 0),
                'end': datetime.datetime(2008, 1, 5, 10, 0),
                'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
                'rule': daily
               })
        self.event2.save()
    
    def test_occurrences_after(self):
        eml = EventListManager([self.event1, self.event2])
        occurrences = eml.occurrences_after(datetime.datetime(2009,4,1,0,0))
        self.assertEqual(occurrences.next().event, self.event1)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event2)
        self.assertEqual(occurrences.next().event, self.event1)
        