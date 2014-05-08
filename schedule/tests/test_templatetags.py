import datetime

from django.test import TestCase

from schedule.templatetags.scheduletags import querystring_for_date

class TestTemplateTags(TestCase):
    
    def test_querystring_for_datetime(self):
        date = datetime.datetime(2008,1,1,0,0,0)
        query_string=querystring_for_date(date)
        self.assertEqual("?year=2008&amp;month=1&amp;day=1&amp;hour=0&amp;minute=0&amp;second=0",
            query_string)
