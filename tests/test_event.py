import datetime
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
import pytz

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from schedule.models import Event, Rule, Calendar, EventRelation


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
                'end_recurring_period': end_recurring,
                'rule': rule,
                'calendar': cal
               })

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
        occurrences_two = event_two.get_occurrences(datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                                                    datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))
        self.assertEqual(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences(datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                                                    datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))
        self.assertEqual(0, len(occurrences_one))

    def test_recurring_event_get_occurrences(self):
        recurring_event = Event(**self.recurring_data)
        occurrences = recurring_event.get_occurrences(start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
                                                      end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(["%s to %s" % (o.start, o.end) for o in occurrences],
                          ['2008-01-12 08:00:00+00:00 to 2008-01-12 09:00:00+00:00',
                           '2008-01-19 08:00:00+00:00 to 2008-01-19 09:00:00+00:00'])

    def test_event_get_occurrences_after(self):

        cal = Calendar(name="MyCal")
        cal.save()
        rule = Rule(frequency="WEEKLY")
        rule.save()

        recurring_event = self.__create_recurring_event(
                    'Recurrent event test get_occurrence',
                    datetime.datetime(2008, 1, 5, 8, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 1, 5, 9, 0, tzinfo=pytz.utc),
                    datetime.datetime(2008, 5, 5, 0, 0, tzinfo=pytz.utc),
                    rule,
                    cal,
                    )
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

        self.assertEqual(1, len(occurrences_two))

        occurrences_one = event_one.get_occurrences(
                                    datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                                    datetime.datetime(2013, 1, 5, 12, 0, tzinfo=pytz.utc))

        self.assertEqual(0, len(occurrences_one))

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
        recurring_event.save()
        occurrences = recurring_event.get_occurrences(
                                    start=datetime.datetime(2008, 1, 12, 0, 0, tzinfo=pytz.utc),
                                    end=datetime.datetime(2008, 1, 20, 0, 0, tzinfo=pytz.utc))

        self.assertEqual(["%s to %s" %(o.start, o.end) for o in occurrences],
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

    def test_prevent_type_error_when_comparing_naive_and_aware_dates(self):
        # this only test if the TypeError is raised
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
        naive_date = datetime.datetime(2008, 1, 20, 0, 0)
        self.assertIsNone(event.get_occurrence(naive_date))

    @override_settings(USE_TZ=False)
    def test_prevent_type_error_when_comparing_dates_when_tz_off(self):
        cal = Calendar(name="MyCal")
        cal.save()
        rule = Rule(frequency = "WEEKLY")
        rule.save()

        event = self.__create_recurring_event(
                    'Recurrent event test get_occurrence',
                    datetime.datetime(2008, 1, 5, 8, 0),
                    datetime.datetime(2008, 1, 5, 9, 0),
                    datetime.datetime(2008, 5, 5, 0, 0),
                    rule,
                    cal,
                    )
        naive_date = datetime.datetime(2008, 1, 20, 0, 0)
        self.assertIsNone(event.get_occurrence(naive_date))

    def test_event_get_ocurrence(self):

        cal = Calendar(name='MyCal')
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            cal)


        occurrence = event.get_occurrence(start)
        self.assertEqual(occurrence.start, start)

    def test_occurences_after_with_no_params(self):

        cal = Calendar(name='MyCal')
        start = timezone.now() + datetime.timedelta(days=1)
        event = self.__create_event(
                            'Non recurring event test get_occurrence',
                            start,
                            start + datetime.timedelta(hours=1),
                            cal)

        occurrences = list(event.occurrences_after())
        self.assertEqual(len(occurrences), 1)
        self.assertEqual(occurrences[0].start, start)
        self.assertEqual(occurrences[0].end, start + datetime.timedelta(hours=1))


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
        self.assertEqual(len(occurrences), 11)

    def test_get_for_object(self):
        user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        event_relations = list(Event.objects.get_for_object(user, 'owner', inherit=False))
        self.assertEqual(len(event_relations), 0)

        rule = Rule(frequency = "DAILY")
        rule.save()
        cal = Calendar(name='MyCal')
        cal.save()
        event = self.__create_event(
                'event test',
                datetime.datetime(2013, 1, 5, 8, 0, tzinfo=pytz.utc),
                datetime.datetime(2013, 1, 5, 9, 0, tzinfo=pytz.utc),
                cal
               )
        event.save()
        events = list(Event.objects.get_for_object(user, 'owner', inherit=False))
        self.assertEqual(len(events), 0)
        EventRelation.objects.create_relation(event, user, 'owner')

        events = list(Event.objects.get_for_object(user, 'owner', inherit=False))
        self.assertEqual(len(events), 1)
        self.assertEqual(event, events[0])

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
        self.assertEqual(reverse('event', kwargs={'event_id': event.id}), url)

    def test_(self):
        pass

class TestEventRelationManager(TestCase):

    def test_get_events_for_object(self):
        pass
