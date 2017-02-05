from __future__ import unicode_literals
from django.utils.six.moves.builtins import str
from django.utils.six import with_metaclass
from dateutil.rrule import (DAILY, MONTHLY, WEEKLY, YEARLY, HOURLY, MINUTELY,
                            SECONDLY)
from dateutil.rrule import (MO, TU, WE, TH, FR, SA, SU)

from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from schedule.utils import get_model_bases

freqs = (("YEARLY", _("Yearly")),
         ("MONTHLY", _("Monthly")),
         ("WEEKLY", _("Weekly")),
         ("DAILY", _("Daily")),
         ("HOURLY", _("Hourly")),
         ("MINUTELY", _("Minutely")),
         ("SECONDLY", _("Secondly")))


@python_2_unicode_compatible
class Rule(with_metaclass(ModelBase, *get_model_bases())):
    """
    This defines a rule by which an event will recur.  This is defined by the
    rrule in the dateutil documentation.

    * name - the human friendly name of this kind of recursion.
    * description - a short description describing this type of recursion.
    * frequency - the base recurrence period
    * param - extra params required to define this type of recursion. The params
      should follow this format:

        param = [rruleparam:value;]*
        rruleparam = see list below
        value = int[,int]*

      The options are: (documentation for these can be found at
      http://labix.org/python-dateutil#head-470fa22b2db72000d7abe698a5783a46b0731b57)
        ** count
        ** bysetpos
        ** bymonth
        ** bymonthday
        ** byyearday
        ** byweekno
        ** byweekday
        ** byhour
        ** byminute
        ** bysecond
        ** byeaster
    """
    name = models.CharField(_("name"), max_length=32)
    description = models.TextField(_("description"))
    frequency = models.CharField(_("frequency"), choices=freqs, max_length=10)
    params = models.TextField(_("params"), null=True, blank=True)

    _week_days = {'MO': MO,
                  'TU': TU,
                  'WE': WE,
                  'TH': TH,
                  'FR': FR,
                  'SA': SA,
                  'SU': SU}

    class Meta(object):
        verbose_name = _('rule')
        verbose_name_plural = _('rules')
        app_label = 'schedule'

    def rrule_frequency(self):
        compatibility_dict = {
            'DAILY': DAILY,
            'MONTHLY': MONTHLY,
            'WEEKLY': WEEKLY,
            'YEARLY': YEARLY,
            'HOURLY': HOURLY,
            'MINUTELY': MINUTELY,
            'SECONDLY': SECONDLY
        }
        return compatibility_dict[self.frequency]

    def _weekday_or_number(self, param):
        '''
        Receives a rrule parameter value, returns a upper case version
        of the value if its a weekday or an integer if its a number
        '''
        try:
            return int(param)
        except (TypeError, ValueError):
            uparam = str(param).upper()
            if uparam in Rule._week_days:
                return Rule._week_days[uparam]

    def get_params(self):
        """
        >>> rule = Rule(params = "count:1;bysecond:1;byminute:1,2,4,5")
        >>> rule.get_params()
        {'count': 1, 'byminute': [1, 2, 4, 5], 'bysecond': 1}
        """
        if self.params is None:
            return {}
        params = self.params.split(';')
        param_dict = []
        for param in params:
            param = param.split(':')
            if len(param) != 2:
                continue

            param = (
                str(param[0]).lower(),
                [x for x in
                 [self._weekday_or_number(v) for v in param[1].split(',')]
                 if x is not None],
            )

            if len(param[1]) == 1:
                param_value = self._weekday_or_number(param[1][0])
                param = (param[0], param_value)
            param_dict.append(param)
        return dict(param_dict)

    def __str__(self):
        """Human readable string for Rule"""
        return 'Rule %s params %s' % (self.name, self.params)
