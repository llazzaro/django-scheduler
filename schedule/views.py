from future import standard_library
standard_library.install_aliases()
import json
import pytz
import datetime
from urllib.parse import quote

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.views.generic.edit import (
        UpdateView, CreateView, DeleteView, ModelFormMixin, ProcessFormView)

from schedule.conf.settings import GET_EVENTS_FUNC, OCCURRENCE_CANCEL_REDIRECT
from schedule.forms import EventForm, OccurrenceForm
from schedule.models import Calendar, Occurrence, Event
from schedule.periods import weekday_names
from schedule.utils import check_event_permissions, check_calendar_permissions, coerce_date_dict

class CalendarViewPermissionMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(CalendarViewPermissionMixin, cls).as_view(**initkwargs)
        return check_calendar_permissions(view)

class EventEditPermissionMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(EventEditPermissionMixin, cls).as_view(**initkwargs)
        return check_event_permissions(view)

class TemplateKwargMixin(TemplateResponseMixin):
    def get_template_names(self):
        if 'template_name' in self.kwargs:
            return [self.kwargs['template_name']]
        else:
            return super(TemplateKwargMixin, self).get_template_names()

class CancelButtonMixin(object):
    def post(self, request, *args, **kwargs):
        next = kwargs.get('next', None)
        self.success_url = get_next_url(request, next)
        if "cancel" in request.POST:
            return HttpResponseRedirect(self.success_url)
        else:
            return super(CancelButtonMixin, self).post(request, *args, **kwargs)

class CalendarMixin(CalendarViewPermissionMixin, TemplateKwargMixin):
    model = Calendar
    slug_url_kwarg = 'calendar_slug'

class CalendarView(CalendarMixin, DetailView):
    template_name = 'schedule/calendar.html'
    
class CalendarByPeriodsView(CalendarMixin, DetailView):
    template_name = 'schedule/calendar_by_period.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, request, **kwargs):
        context = super(CalendarByPeriodsView, self).get_context_data(**kwargs)
        calendar = self.object
        periods = kwargs.get('periods', None)
        try:
            date = coerce_date_dict(request.GET)
        except ValueError:
            raise Http404
        if date:
            try:
                date = datetime.datetime(**date)
            except ValueError:
                raise Http404
        else:
            date = timezone.now()
        event_list = GET_EVENTS_FUNC(request, calendar)

        if 'django_timezone' in self.request.session:
            local_timezone = pytz.timezone(request.session['django_timezone'])
        else:
            local_timezone = timezone.get_default_timezone()
        period_objects = {} 
        for period in periods:
            if period.__name__.lower() == 'year':
                period_objects[period.__name__.lower()] = period(event_list, date, None, local_timezone) 
            else:
                period_objects[period.__name__.lower()] = period(event_list, date, None, None, local_timezone)

        context.update({
            'date': date,
            'periods': period_objects,
            'calendar': calendar,
            'weekday_names': weekday_names,
            'here': quote(request.get_full_path()),
        })
        return context

class OccurrenceMixin(CalendarViewPermissionMixin, TemplateKwargMixin):
    model = Occurrence
    pk_url_kwarg = 'occurrence_id'
    form_class = OccurrenceForm

class OccurrenceEditMixin(EventEditPermissionMixin, OccurrenceMixin, CancelButtonMixin):
    def get_initial(self):
        initial_data = super(OccurrenceEditMixin, self).get_initial()
        event, self.object = get_occurrence(**self.kwargs)
        return initial_data

class OccurrenceView(OccurrenceMixin, DetailView):
    template_name = 'schedule/occurrence.html'

class OccurrencePreview(OccurrenceMixin, ModelFormMixin, ProcessFormView):
    template_name = 'schedule/occurrence.html'

    def get_context_data(self, **kwargs):
        context = super(OccurrencePreview, self).get_context_data()
        context = {
            'event': self.object.event,
            'occurrence': self.object,
        }
        return context

class EditOccurrenceView(OccurrenceEditMixin, UpdateView):
    template_name = 'schedule/edit_occurrence.html'

class CreateOccurrenceView(OccurrenceEditMixin, CreateView):
    template_name = 'schedule/edit_occurrence.html'

class CancelOccurrenceView(OccurrenceEditMixin, ModelFormMixin, ProcessFormView):
    template_name = 'schedule/cancel_occurrence.html'

    def post(self, request, *args, **kwargs):
        event, occurrence = get_occurrence(**kwargs)
        self.success_url = kwargs.get('next',
                        get_next_url(request, event.get_absolute_url()))
        if "cancel" not in request.POST:
            occurrence.cancel()
        return HttpResponseRedirect(self.success_url)

class EventMixin(CalendarViewPermissionMixin, TemplateKwargMixin):
    model = Event
    pk_url_kwarg = 'event_id'

class EventEditMixin(EventEditPermissionMixin, EventMixin, CancelButtonMixin):
    pass

class EventView(EventMixin, DetailView):
    template_name = 'schedule/event.html'

class EditEventView(EventEditMixin, UpdateView):
    form_class = EventForm
    template_name = 'schedule/create_event.html'

class CreateEventView(EventEditMixin, CreateView):
    form_class = EventForm
    template_name = 'schedule/create_event.html'

    def get_initial(self):
        date = coerce_date_dict(self.request.GET)
        initial_data = None
        if date:
            try:
                start = datetime.datetime(**date)
                initial_data = {
                    "start": start,
                    "end": start + datetime.timedelta(minutes=30)
                }
            except TypeError:
                raise Http404
            except ValueError:
                raise Http404
        return initial_data

    def form_valid(self, form): 
        event = form.save(commit=False)
        event.creator = self.request.user
        event.calendar = get_object_or_404(Calendar, slug=self.kwargs['calendar_slug'])
        event.save()
        return HttpResponseRedirect(event.get_absolute_url())

class DeleteEventView(EventEditMixin, DeleteView):
    template_name = 'schedule/delete_event.html'

def get_occurrence(event_id, occurrence_id=None, year=None, month=None, day=None, hour=None, minute=None, second=None):
    """
    Because occurrences don't have to be persisted, there must be two ways to
    retrieve them. both need an event, but if its persisted the occurrence can
    be retrieved with an id. If it is not persisted it takes a date to
    retrieve it.  This function returns an event and occurrence regardless of
    which method is used.
    """
    if(occurrence_id):
        occurrence = get_object_or_404(Occurrence, id=occurrence_id)
        event = occurrence.event
    elif(all((year, month, day, hour, minute, second))):
        event = get_object_or_404(Event, id=event_id)
        occurrence = event.get_occurrence(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second)))
        if occurrence is None:
            raise Http404
    else:
        raise Http404
    return event, occurrence

def check_next_url(next):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if not next or '://' in next:
        return None
    return next

def get_next_url(request, default):
    next = default
    if OCCURRENCE_CANCEL_REDIRECT:
        next = OCCURRENCE_CANCEL_REDIRECT
    if 'next' in request.REQUEST and check_next_url(request.REQUEST['next']) is not None:
        next = request.REQUEST['next']
    return next


def api_occurrences(request):
    utc=pytz.UTC
    # version 2 of full calendar
    if '-' in request.GET.get('start'):
        convert = lambda d: datetime.datetime.strptime(d, '%Y-%m-%d')
    else:
        convert = lambda d: datetime.datetime.utcfromtimestamp(float(d))
    start = utc.localize(convert(request.GET.get('start')))
    end = utc.localize(convert(request.GET.get('end')))
    calendar = get_object_or_404(Calendar, slug=request.GET.get('calendar_slug'))
    response_data =[]
    for event in calendar.events.filter(start__gte=start, end__lte=end):
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            response_data.append({
                "id": occurrence.id,
                "title": occurrence.title,
                "start": occurrence.start.isoformat(),
                "end": occurrence.end.isoformat(),
            })
    return HttpResponse(json.dumps(response_data), content_type="application/json")
