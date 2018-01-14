from __future__ import unicode_literals

from django.forms.widgets import Input


class ColorInput(Input):
    input_type = 'color'
