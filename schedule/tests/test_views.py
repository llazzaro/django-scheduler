from django.test import TestCase
from schedule.views import  calendar_detail, calendar_by_periods, check_next_url, coerce_date_dict


class TestViewUtils(TestCase):
    
    def test_check_next_url(self):
        url = "http://thauber.com"
        self.assertTrue(check_next_url(url) is None)
        url = "/hello/world/"
        self.assertEqual(url, check_next_url(url))
    
    def test_coerce_date_dict(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'day': '2', 'hour': '4', 'minute': '4', 'second': '4'}),
            {'year': 2008, 'month': 4, 'day': 2, 'hour': 4, 'minute': 4, 'second': 4}
            )
    
    def test_coerce_date_dict_partial(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'day': '2'}),
            {'year': 2008, 'month': 4, 'day': 2, 'hour': 0, 'minute': 0, 'second': 0}           
            )
    
    def test_coerce_date_dict_empty(self):
        self.assertEqual(
            coerce_date_dict({}),
            {}
            )
    
    def test_coerce_date_dict_missing_values(self):
        self.assertEqual(
            coerce_date_dict({'year': '2008', 'month': '4', 'hours': '3'}),
            {'year': 2008, 'month': 4, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0}           
            )
    
class TestCalendarView(TestCase):
    
    def setUp(self):
        self.calendar = Calendar(name="Cal", slug=cal)
        self.calendar.save()

    
    