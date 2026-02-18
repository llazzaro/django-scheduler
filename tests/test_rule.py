from dateutil.rrule import FR
from django.test import TestCase

from schedule.models import Rule
from schedule.models.rules import RuleParam, RuleParamVariant


class TestPeriod(TestCase):
    def test_get_params(self):
        rule = Rule.objects.create(
            name="test_rule",
            frequency="WEEKLY",
            params="count:1;bysecond:1;byminute:1,2,4,5;byweekday:FR;bysetpos:-1",
        )
        expected = {
            "count": 1,
            "byminute": [1, 2, 4, 5],
            "bysecond": 1,
            "byweekday": FR,
            "bysetpos": -1,
        }
        self.assertEqual(rule.get_params(), expected)


class TestRuleParam(TestCase):
    def test_ruleparam_str(self):
        param = RuleParam.objects.create(
            name="testparam", display_string="test display"
        )
        self.assertEqual(str(param), "test display")

    def test_ruleparamvariant_str(self):
        param = RuleParam.objects.create(
            name="testparam", display_string="test display"
        )
        variant = RuleParamVariant.objects.create(
            param=param, value=42, value_display_string="forty-two"
        )
        self.assertIn("test display", str(variant))
        self.assertIn("forty-two", str(variant))

    def test_get_params_with_m2m_repeats(self):
        param = RuleParam.objects.get(name="byweekday")
        mo_variant = RuleParamVariant.objects.get(param=param, value=0)
        tu_variant = RuleParamVariant.objects.get(param=param, value=1)
        rule = Rule.objects.create(name="m2m_rule", frequency="WEEKLY", params="")
        rule.repeats.add(mo_variant, tu_variant)
        result = rule.get_params()
        self.assertEqual(result["byweekday"], [0, 1])

    def test_get_params_text_overrides_m2m(self):
        param = RuleParam.objects.get(name="byweekday")
        mo_variant = RuleParamVariant.objects.get(param=param, value=0)
        rule = Rule.objects.create(
            name="override_rule", frequency="WEEKLY", params="byweekday:FR"
        )
        rule.repeats.add(mo_variant)
        result = rule.get_params()
        self.assertEqual(result["byweekday"], FR)

    def test_ensure_rule_creates_new(self):
        rule = Rule.ensure_rule("WEEKLY", {"byweekday": [0, 1]})
        self.assertIsNotNone(rule.pk)
        self.assertEqual(rule.frequency, "WEEKLY")
        param_names = {r.param.name for r in rule.repeats.all()}
        self.assertEqual(param_names, {"byweekday"})
        values = sorted(r.value for r in rule.repeats.all())
        self.assertEqual(values, [0, 1])

    def test_ensure_rule_returns_existing(self):
        rule1 = Rule.ensure_rule("WEEKLY", {"byweekday": [0, 1]})
        rule2 = Rule.ensure_rule("WEEKLY", {"byweekday": [0, 1]})
        self.assertEqual(rule1.pk, rule2.pk)

    def test_ensure_rule_invalid_param(self):
        with self.assertRaises(ValueError):
            Rule.ensure_rule("WEEKLY", {"count": [1]})

    def test_rule_str_unsaved(self):
        rule = Rule(name="unsaved", frequency="DAILY", params="count:1")
        result = str(rule)
        self.assertIn("unsaved", result)
        self.assertIn("count:1", result)

    def test_rule_str_saved(self):
        rule = Rule.objects.create(
            name="saved_rule", frequency="DAILY", params="count:1"
        )
        result = str(rule)
        self.assertIn("saved_rule", result)
