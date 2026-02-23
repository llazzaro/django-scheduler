from django.forms.widgets import TextInput


class ColorInput(TextInput):
    input_type = "color"

    def __init__(self, *args, **kwargs):
        TextInput.__init__(self, *args, **kwargs)
        self.attrs.update(
            {
                "type": "color",
            }
        )

    def render(self, name, value, attrs=None, renderer=None):
        return TextInput.render(self, name, value, attrs, renderer)
