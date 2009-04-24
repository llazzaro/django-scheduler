from django import forms
from django.utils.translation import ugettext_lazy as _
from schedule.models import Event, Occurrence
import datetime
import time


class EventForm(forms.ModelForm):
    def __init__(self, hour24=False, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
    
    start = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    end = forms.DateTimeField(widget=forms.SplitDateTimeWidget, help_text = _("The end time must be later than start time."))
    end_recurring_period = forms.DateTimeField(help_text = _("This date is ignored for one time only events."), required=False)
    
    class Meta:
        model = Event
        exclude = ('creator', 'created_on', 'calendar')
        

class OccurrenceForm(forms.ModelForm):

    start = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    end = forms.DateTimeField(widget=forms.SplitDateTimeWidget, help_text = _("The end time must be later than start time."))
    
    class Meta:
        model = Occurrence
        exclude = ('original_start', 'original_end', 'event', 'cancelled')
