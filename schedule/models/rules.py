from dateutil.rrule import (
    DAILY,
    FR,
    HOURLY,
    MINUTELY,
    MO,
    MONTHLY,
    SA,
    SECONDLY,
    SU,
    TH,
    TU,
    WE,
    WEEKLY,
    YEARLY,
)
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

freqs = (
    ("YEARLY", _("Yearly")),
    ("MONTHLY", _("Monthly")),
    ("WEEKLY", _("Weekly")),
    ("DAILY", _("Daily")),
    ("HOURLY", _("Hourly")),
    ("MINUTELY", _("Minutely")),
    ("SECONDLY", _("Secondly")),
)

# See also https://stackoverflow.com/questions/3582544/django-model-choice-option-as-a-multi-select-box for a way more complicated way


class RuleParam(models.Model):
    name = models.CharField(_("name"), max_length=32, unique=True)
    display_string = models.CharField(_("display string"), max_length=32, unique=True)

    # variants = related fields
    def __str__(self):
        return f"{_(self.display_string)}"

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]


class RuleParamVariant(models.Model):
    param = models.ForeignKey(
        RuleParam,
        on_delete=models.CASCADE,
        verbose_name=_("Possible value"),
        related_name="variant_set",
    )
    value = models.IntegerField(_("value"))
    value_display_string = models.CharField(_("value display string"), max_length=32)

    def __str__(self):
        return f"{self.param} {_(self.value_display_string)}"

    class Meta:
        indexes = [
            models.Index(fields=["param"]),
        ]
        unique_together = [["param", "value"]]
        ordering = ["param", "value"]


class Rule(models.Model):
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
      https://dateutil.readthedocs.io/en/stable/rrule.html#module-dateutil.rrule
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

    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"))
    frequency = models.CharField(_("frequency"), choices=freqs, max_length=10)
    repeats = models.ManyToManyField(RuleParamVariant, blank=True)
    params = models.TextField(_("params"), blank=True)

    _week_days = {"MO": MO, "TU": TU, "WE": WE, "TH": TH, "FR": FR, "SA": SA, "SU": SU}

    class Meta:
        verbose_name = _("rule")
        verbose_name_plural = _("rules")

    def rrule_frequency(self):
        compatibility_dict = {
            "DAILY": DAILY,
            "MONTHLY": MONTHLY,
            "WEEKLY": WEEKLY,
            "YEARLY": YEARLY,
            "HOURLY": HOURLY,
            "MINUTELY": MINUTELY,
            "SECONDLY": SECONDLY,
        }
        return compatibility_dict[self.frequency]

    def _weekday_or_number(self, param):
        """
        Receives a rrule parameter value, returns a upper case version
        of the value if its a weekday or an integer if its a number
        """
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
        params = self.params.split(";")
        param_dict = []
        # Prefer the entry in self.params for backward compat.
        for param in params:
            param = param.split(":")
            if len(param) != 2:
                continue

            param = (
                str(param[0]).lower(),
                [
                    x
                    for x in [self._weekday_or_number(v) for v in param[1].split(",")]
                    if x is not None
                ],
            )

            if len(param[1]) == 1:
                param_value = self._weekday_or_number(param[1][0])
                param = (param[0], param_value)
            param_dict.append(param)
        result = dict(param_dict)
        for repeat in self.repeats.all():
            if repeat.param.name not in result:
                result[repeat.param.name] = [
                    x.value for x in self.repeats.all() if x.param == repeat.param
                ]

        return result

    @classmethod
    @transaction.atomic
    def ensure_rule(klass, frequency, by_details):
        """
        Ensure that at least one rule exists with FREQUENCY and BY_DETAILS. If it doesn't exist, create it.
        Return such a rule.

        by_details = {
            byweekno: [1,2,3],
            ...
        }
        """
        repeats = set()
        for key, values in by_details.items():
            if not key.startswith("by"):
                raise ValueError(
                    "Recurrence parameter '{}' must start with 'by'".format(key)
                )
            ruleparam = RuleParam.objects.get(name=key)
            variants = ruleparam.variant_set.filter(value__in=values)
            repeats = repeats.union(variants)

        rules = Rule.objects.filter(frequency=frequency, params="").all()
        for rule in rules:
            if {repeat.id for repeat in rule.repeats.all()} == {
                repeat.id for repeat in repeats
            }:
                return rule

        name = frequency
        for key in by_details.keys():
            local_repeats = [repeat for repeat in repeats if repeat.param.name == key]
            if len(local_repeats) > 0:
                name = name + (
                    ";{}={}".format(
                        key,
                        ",".join(sorted(str(repeat.value) for repeat in local_repeats)),
                    )
                )
        rule = Rule(name=name, frequency=frequency, params="")
        rule.save()  # so it gets an id
        for repeat in repeats:
            rule.repeats.add(repeat)
        return rule

    def __str__(self):
        """Human readable string for Rule"""
        if self.pk:
            return "Rule {} params {}".format(self.name, self.get_params())
        # M2M fields can't exist on unsaved instances, so fall back to the text field.
        return "Rule {} params {}".format(self.name, self.params)
