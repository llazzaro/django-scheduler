import datetime
import os

from django.test import TestCase
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

