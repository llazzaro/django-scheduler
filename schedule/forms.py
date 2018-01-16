from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from schedule.utils import get_event_model, get_occurrence_model
from schedule.widgets import ColorInput


class SpanForm(forms.ModelForm):
    start = forms.SplitDateTimeField(label=_("start"))
    end = forms.SplitDateTimeField(label=_("end"),
                                   help_text=_("The end time must be later than start time."))

    def clean(self):
        if 'end' in self.cleaned_data and 'start' in self.cleaned_data:
            if self.cleaned_data['end'] <= self.cleaned_data['start']:
                raise forms.ValidationError(_("The end time must be later than start time."))
        return self.cleaned_data


class EventForm(SpanForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

    end_recurring_period = forms.DateTimeField(label=_("End recurring period"),
                                               help_text=_("This date is ignored for one time only events."),
                                               required=False)

    class Meta(object):
        model = get_event_model()
        exclude = ('creator', 'created_on', 'calendar')


class OccurrenceForm(SpanForm):
    class Meta(object):
        model = get_occurrence_model()
        exclude = ('original_start', 'original_end', 'event', 'cancelled')


class EventAdminForm(forms.ModelForm):
    class Meta:
        exclude = []
        model = get_event_model()
        widgets = {
            'color_event': ColorInput,
        }
