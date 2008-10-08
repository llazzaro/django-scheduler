from schedule.forms import GlobalSplitDateTimeWidget
import datetime
class GlobalSplitDateTimeWidgetTest(object):
    """
    >>> widget = GlobalSplitDateTimeWidget()
    >>> value = datetime.datetime(2008, 1, 1, 5, 5)
    >>> widget.decompress(value)
    [datetime.date(2008, 1, 1), '05:05', 'AM']
    >>> data = {'datetime_0':'2008-1-1', 'datetime_1':'5:05', 'datetime_2': 'PM'}
    >>> widget.value_from_datadict(data, None, 'datetime')
    datetime.datetime(2008, 1, 1, 17, 5)
    >>> widget = GlobalSplitDateTimeWidget(hour24 = True)
    >>> widget.value_from_datadict(data, None, 'datetime')
    ['2008-1-1', '5:05']
    """
    pass