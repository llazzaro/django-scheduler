from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO


class TestManagementCommand(TestCase):
    def test_command_output(self):
        out = StringIO()
        call_command('load_example_data', stdout=out)
        self.assertIn('', out.getvalue())
        call_command('load_sample_data', stdout=out)
        self.assertIn('', out.getvalue())

