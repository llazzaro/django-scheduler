
import datetime
import pytz

from django.test import TestCase
from django.utils import timezone

from schedule.models import Event, Rule, Calendar, Occurrence, CalendarRelation
from schedule.periods import Period, Day

class TestCalendar(TestCase):

    def setup(self):
        pass

    def __create_event(self, start, end):
        data = {
                'title': 'Recent Event',
                'start': start,
                'end': end
            }
        return Event(**data)


    def test_get_recent_events_without_events_is_empty(self):
        calendar = Calendar()
        self.assertEqual(list(calendar.get_recent()), [])

    def test_get_recent_events_with_events_return_the_event(self):
        pass

    def test_occurrences_after_without_events_is_empty(self):
        calendar = Calendar()
        self.assertEqual(list(calendar.occurrences_after(timezone.now())), [])

    def test_occurrences_after_with_events_after_returns_events(self):
        calendar = Calendar()
        calendar.save()
        start_after = timezone.now() + datetime.timedelta(days=1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = self.__create_event(start_after, end_after)
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].start, start_after)
        self.assertEqual(occurrences[0].end, end_after)

    def test_occurrences_after_with_events_before_returns_empty(self):
        calendar = Calendar()
        calendar.save()
        start_after = timezone.now() + datetime.timedelta(days=-1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = self.__create_event(start_after, end_after)
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEqual(occurrences, [])
#        self.assertEqual(list(calendar.occurrences_after(timezone.now())), [])

#    def test_get_absolute_url(self):
#        calendar = Calendar()
#        self.assertEqual(calendar.get_absolute_url(), '')

    def test_get_calendar_for_object(self):
        calendar = Calendar(name='My Cal')
        calendar.save()
        rule = Rule()
        rule.save()
        calendar.create_relation(rule)
        result = Calendar.objects.get_calendar_for_object(rule)
        self.assertEqual(result.name, 'My Cal')

    def test_get_calendar_for_object_without_calendars(self):
        with self.assertRaises(Calendar.DoesNotExist):
            rule = Rule()
            rule.save()
            Calendar.objects.get_calendar_for_object(rule)

    def test_get_calendar_for_object_with_more_than_one_calendar(self):
        calendar_1 = Calendar(name='My Cal 1')
        calendar_1.save()
        calendar_2 = Calendar(name='My Cal 2')
        calendar_2.save()
        rule = Rule()
        rule.save()
        calendar_1.create_relation(rule)
        calendar_2.create_relation(rule)
        with self.assertRaises(AssertionError):
            result = Calendar.objects.get_calendar_for_object(rule)

    def test_get_or_create_calendar_for_object_without_calendar(self):
        """
            Creation test
        """
        rule = Rule()
        rule.save()
        calendar = Calendar.objects.get_or_create_calendar_for_object(rule, name='My Cal')
        self.assertEqual(calendar.name, 'My Cal')
        calendar_from_rule = Calendar.objects.get_calendars_for_object(rule)[0]
        self.assertEqual(calendar, calendar_from_rule)

    def test_get_or_create_calendar_for_object_withouth_name(self):
        """
            Test with already created calendar
        """
        rule = Rule()
        rule.save()
        calendar = Calendar.objects.get_or_create_calendar_for_object(rule)
        calendar_from_rule = Calendar.objects.get_calendars_for_object(rule)[0]
        self.assertEqual(calendar, calendar_from_rule)

    def test_get_calendars_for_object_without_calendars(self):
        rule = Rule()
        rule.save()
        calendar = Calendar.objects.get_or_create_calendar_for_object(rule, name='My Cal', distinction='owner')
        rule = Rule()
        rule.save()
        calendars = list(Calendar.objects.get_calendars_for_object(rule, distinction='owner'))
        self.assertEqual(len(calendars), 0)

    def test_calendar_absolute_and_event_url(self):
        """
            this test seems to not make too much send, just added since an
            url was with wrong reverse name.

        """
        rule = Rule()
        rule.save()
        calendar = Calendar.objects.get_or_create_calendar_for_object(rule, name='My Cal', distinction='owner')
        abs_url = calendar.get_absolute_url()
        calendar.add_event_url()
        relation = CalendarRelation.objects.create_relation(calendar, rule)
        relation.__unicode__()
