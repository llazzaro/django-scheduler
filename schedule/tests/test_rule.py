import datetime
import pytz

from django.test import TestCase

from schedule.models import Rule

class TestPeriod(TestCase):

    def setUp(self):
        pass

    def test_get_params(self):
        rule = Rule(params = "count:1;bysecond:1;byminute:1,2,4,5")
        expected =  {'count': 1, 'byminute': [1, 2, 4, 5], 'bysecond': 1}
        self.assertEqual(rule.get_params(), expected)
