import datetime
import pytz

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from schedule.models import Event, Rule, Calendar
from schedule.periods import Period, Day

class TestEvent(TestCase):

    def setUp(self):
        cal = Calendar(name="MyCal")
        cal.save()

    def __create_event(self, title, start, end, cal):
        return Event(**{
                'title': title,
                'start': start,
                'end': end,
                'calendar': cal
               })

    def __create_recurring_event(self, title, start, end, end_recurring, rule, cal):
         return Event(**{
                'title': title,
                'start': start,
                'end': end,
                'end_recurring_period' : end_recurring,
                'rule': rule,
                'calendar': cal
               })

    def test_edge_case_events(self):
        cal = Calendar(name="MyCal")
        cal.save()
        event_one = self.__create_event(
                'Edge case event test one',
                datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
                datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                cal
               )
        event_two = self.__create_event(
                'Edge case event test two',
                datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc),
                cal
               )
        event_one.save()
        event_two.save()
        occurrences_two = event_two.get_occurrences(
                                    datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                                    datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))

        self.assertEquals(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences(
                                    datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                                    datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))

        self.assertEquals(0, len(occurrences_one))

    def test_recurring_event_get_occurrences(self):
        cal = Calendar(name="MyCal")
        rule = Rule(frequency = "WEEKLY")
        rule.save()

        recurring_event = self.__create_recurring_event(
                                    'Recurring event test',
                                    datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                                    datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                                    datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                                    rule,
                                    cal
                )
        occurrences = recurring_event.get_occurrences(
                                    start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
                                    end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc))

        self.assertEquals(["%s to %s" %(o.start, o.end) for o in occurrences],
                ['2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00', '2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00'])

    def test_recurring_event_get_occurrences_after(self):

        cal = Calendar(name="MyCal")
        cal.save()
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        recurring_event= self.__create_recurring_event(
                    'Recurrent event test get_occurrence',
                    datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                    rule,
                    cal,
                    )

        recurring_event.save()
        #occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 5, tzinfo=pytz.utc),
        #    end = datetime.datetime(2008, 1, 6, tzinfo=pytz.utc))
        #occurrence = occurrences[0]
        #occurrence2 = recurring_event.occurrences_after(datetime.datetime(2008, 1, 5, tzinfo=pytz.utc)).next()
        #self.assertEqual(occurrence, occurrence2)

    def test_recurring_event_get_occurrence(self):

        cal = Calendar(name="MyCal")
        cal.save()
        rule = Rule(frequency = "WEEKLY")
        rule.save()

        event = self.__create_recurring_event(
                    'Recurrent event test get_occurrence',
                    datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                    rule,
                    cal,
                    )
        event.save()
        occurrence = event.get_occurrence(datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc))
        self.assertEqual(occurrence.start, datetime.datetime(2008, 1, 5, 8, tzinfo=pytz.utc))
        occurrence.save()
        occurrence = event.get_occurrence(datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc))
        self.assertTrue(occurrence.pk is not None)

    def test_event_get_ocurrence(self):

        cal = Calendar(name='MyCal')
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            cal)


        occurrence = event.get_occurrence(start)
        self.assertEquals(occurrence.start, start)

    def test_occurences_after_with_no_params(self):

        cal = Calendar(name='MyCal')
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            cal)

        occurrences = list(event.occurrences_after())
        self.assertEquals(len(occurrences), 1)
        self.assertEquals(occurrences[0].start, start)
        self.assertEquals(occurrences[0].end, start + datetime.timedelta(hours=1))


    def test_occurences_with_recurrent_event_end_recurring_period_edge_case(self):

        cal = Calendar(name='MyCal')

        rule = Rule(frequency = "DAILY")
        rule.save()
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            start + datetime.timedelta(days=10),
                            rule,
                            cal)
        occurrences = list(event.occurrences_after())
        self.assertEquals(len(occurrences), 11)

    def test_get_for_object(self):
        user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        event_relations = list(Event.objects.get_for_object(user, 'owner', inherit=False))
        self.assertEquals(len(event_relations), 1)
        self.assertEquals(rule, event_relations[0].content_object)

    def test_get_absolute(self):
        cal = Calendar(name='MyCal')
        cal.save()
        rule = Rule(frequency = "DAILY")
        rule.save()
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_recurring_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            start + datetime.timedelta(days=10),
                            rule,
                            cal)
        event.save()
        url = event.get_absolute_url()
        self.assertEquals('/event/1/', url)

    def test_(self):
        pass

class TestEventRelationManager(TestCase):

    def test_get_events_for_object(self):
        pass
