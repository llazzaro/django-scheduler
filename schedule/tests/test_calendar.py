
import datetime
import pytz

from django.test import TestCase
from django.utils import timezone

from schedule.models import Event, Rule, Calendar, Occurrence
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
        self.assertEquals(list(calendar.get_recent()), [])

    def test_get_recent_events_with_events_return_the_event(self):
        pass

    def test_occurrences_after_without_events_is_empty(self):
        calendar = Calendar()
        self.assertEquals(list(calendar.occurrences_after(timezone.now())), [])

    def test_occurrences_after_with_events_after_returns_events(self):
        calendar = Calendar()
        calendar.save()
        start_after = timezone.now() + datetime.timedelta(days=1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = self.__create_event(start_after, end_after)
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEquals(len(occurrences), 1)
        self.assertEquals(occurrences[0].start, start_after)
        self.assertEquals(occurrences[0].end, end_after)

    def test_occurrences_after_with_events_before_returns_empty(self):
        calendar = Calendar()
        calendar.save()
        start_after = timezone.now() + datetime.timedelta(days=-1)
        end_after = start_after + datetime.timedelta(hours=1)
        event = self.__create_event(start_after, end_after)
        calendar.events.add(event)
        occurrences = list(calendar.occurrences_after(timezone.now()))
        self.assertEquals(occurrences, [])
#        self.assertEquals(list(calendar.occurrences_after(timezone.now())), [])

#    def test_get_absolute_url(self):
#        calendar = Calendar()
#        self.assertEquals(calendar.get_absolute_url(), '')

    def test_get_calendar_for_object(self):
        calendar = Calendar(name='My Cal')
        calendar.save()
        rule = Rule()
        rule.save()
        calendar.create_relation(rule)
        result = Calendar.objects.get_calendar_for_object(rule)
        self.assertFalse(result.name, 'My Cal')
