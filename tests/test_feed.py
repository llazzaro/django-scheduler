import datetime

from django.test import TestCase

from schedule.feeds.atom import rfc3339_date, get_tag_uri

class Testatom(TestCase):

    def test_rfc3339_date(self):
        date = datetime.datetime(2014, 2, 25, 19, 30, 40, 573234)
        result = rfc3339_date(date)
        expected = '2014-2-25T19:30:40Z'
        self.assertEqual(result, expected)

    def test_get_tag_uri(self):
        date = datetime.datetime(2014, 2, 25, 19, 30, 40, 573234)
        result = get_tag_uri('/sarasa/', date)
        expected = 'tag:,2014-2-25:/sarasa/'
        self.assertEqual(result, expected)
