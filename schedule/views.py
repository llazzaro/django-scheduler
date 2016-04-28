import json
import pytz
import datetime
import dateutil.parser
from django.utils.six.moves.urllib.parse import quote

from django.db.models import Q, F
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import (
        UpdateView, CreateView, DeleteView, ModelFormMixin, ProcessFormView)
from django.utils.http import is_safe_url

from schedule.conf.settings import (GET_EVENTS_FUNC, OCCURRENCE_CANCEL_REDIRECT,
                                    EVENT_NAME_PLACEHOLDER, CHECK_EVENT_PERM_FUNC, 
                                    CHECK_OCCURRENCE_PERM_FUNC, USE_FULLCALENDAR)
from schedule.forms import EventForm, OccurrenceForm
from schedule.models import Calendar, Occurrence, Event
from schedule.periods import weekday_names
from schedule.utils import (check_event_permissions, 
    check_calendar_permissions, coerce_date_dict, 
    check_occurrence_permissions)


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

class OccurrenceEditPermissionMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(OccurrenceEditPermissionMixin, cls).as_view(**initkwargs)
        return check_occurrence_permissions(view)


class TemplateKwargMixin(TemplateResponseMixin):
    def get_template_names(self):
        if 'template_name' in self.kwargs:
            return [self.kwargs['template_name']]
        else:
            return super(TemplateKwargMixin, self).get_template_names()


class CancelButtonMixin(object):
    def post(self, request, *args, **kwargs):
        next_url = kwargs.get('next', None)
        self.success_url = get_next_url(request, next_url)
        if "cancel" in request.POST:
            return HttpResponseRedirect(self.success_url)
        else:
            return super(CancelButtonMixin, self).post(request, *args, **kwargs)


class CalendarMixin(CalendarViewPermissionMixin, TemplateKwargMixin):
    model = Calendar
    slug_url_kwarg = 'calendar_slug'


class CalendarView(CalendarMixin, DetailView):
    template_name = 'schedule/calendar.html'


class FullCalendarView(CalendarMixin, DetailView):
    template_name="fullcalendar.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(FullCalendarView, self).get_context_data()
        context = {
            'calendar_slug': kwargs.get('calendar_slug'),
        }
        return context


class CalendarByPeriodsView(CalendarMixin, DetailView):
    template_name = 'schedule/calendar_by_period.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, request, **kwargs):
        context = super(CalendarByPeriodsView, self).get_context_data(**kwargs)
        calendar = self.object
        period_class = kwargs['period']
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

        local_timezone = timezone.get_current_timezone()
        period = period_class(event_list, date, tzinfo=local_timezone)

        context.update({
            'date': date,
            'period': period,
            'calendar': calendar,
            'weekday_names': weekday_names,
            'here': quote(request.get_full_path()),
        })
        return context


class OccurrenceMixin(CalendarViewPermissionMixin, TemplateKwargMixin):
    model = Occurrence
    pk_url_kwarg = 'occurrence_id'
    form_class = OccurrenceForm


class OccurrenceEditMixin(CancelButtonMixin, OccurrenceEditPermissionMixin, OccurrenceMixin):
    def get_initial(self):
        initial_data = super(OccurrenceEditMixin, self).get_initial()
        _, self.object = get_occurrence(**self.kwargs)
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


class EventEditMixin(CancelButtonMixin, EventEditPermissionMixin, EventMixin):
    pass


class EventView(EventMixin, DetailView):
    template_name = 'schedule/event.html'


class EditEventView(EventEditMixin, UpdateView):
    form_class = EventForm
    template_name = 'schedule/create_event.html'

    def form_valid(self, form):
        event = form.save(commit=False)
        old_event = Event.objects.get(pk=event.pk)
        dts = datetime.timedelta(minutes=
            int((event.start-old_event.start).total_seconds() / 60)
        )
        dte = datetime.timedelta(minutes=
            int((event.end-old_event.end).total_seconds() / 60)
        )
        event.occurrence_set.all().update(
            original_start=F('original_start') + dts,
            original_end=F('original_end') + dte,
        )
        event.save()
        return super(EditEventView, self).form_valid(form)


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

    def get_context_data(self, **kwargs):
        ctx = super(DeleteEventView, self).get_context_data(**kwargs)
        ctx['next'] = self.get_success_url()
        return ctx

    def get_success_url(self):
        """
        After the event is deleted there are three options for redirect, tried in
        this order:
        # Try to find a 'next' GET variable
        # If the key word argument redirect is set
        # Lastly redirect to the event detail of the recently create event
        """
        url_val = 'fullcalendar' if USE_FULLCALENDAR else 'day_calendar'
        next_url = self.kwargs.get('next') or reverse(url_val, args=[self.object.calendar.slug])
        next_url = get_next_url(self.request, next_url)
        return next_url


def get_occurrence(event_id, occurrence_id=None, year=None, month=None,
                   day=None, hour=None, minute=None, second=None,
                   tzinfo=pytz.utc):
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
            datetime.datetime(int(year), int(month), int(day), int(hour),
                              int(minute), int(second), tzinfo=tzinfo))
        if occurrence is None:
            raise Http404
    else:
        raise Http404
    return event, occurrence


def check_next_url(next_url):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if not next_url or '://' in next_url:
        return None
    return next_url


def get_next_url(request, default):
    next_url = default
    if OCCURRENCE_CANCEL_REDIRECT:
        next_url = OCCURRENCE_CANCEL_REDIRECT
    _next_url = request.GET.get('next') if request.method in ['GET', 'HEAD'] else request.POST.get('next')
    if _next_url and is_safe_url(url=_next_url, host=request.get_host()):
        next_url = _next_url
    return next_url

@check_calendar_permissions
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
    if Occurrence.objects.all().count() > 0:
        i = Occurrence.objects.latest('id').id + 1
    else:
        i = 1
    event_list = calendar.events.filter(start__lte=end).filter(
        Q(end_recurring_period__gte=start) | Q(end_recurring_period__isnull=True) )
    for event in event_list:
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            if occurrence.id:
                occurrence_id = occurrence.id
                existed = True
            else:
                occurrence_id = i + occurrence.event.id
                existed = False
            response_data.append({
                "id": occurrence_id,
                "title": occurrence.title,
                "start": occurrence.start.isoformat(),
                "end": occurrence.end.isoformat(),
                "existed" : existed,
                "event_id" : occurrence.event.id,
            })
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@check_calendar_permissions
def api_move_or_resize_by_code(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        existed = (request.POST.get('existed') == 'true')
        dt = datetime.timedelta(minutes=int(request.POST.get('delta')))
        resize = bool(request.POST.get('resize', False))
        resp = {}
        resp['status'] = "PERMISSION DENIED"

        if existed:
            occurrence = Occurrence.objects.get(id=id)
            occurrence.end += dt
            if not resize:
                occurrence.start += dt
            if CHECK_OCCURRENCE_PERM_FUNC(occurrence, request.user):
                occurrence.save()
                resp['status'] = "OK"
        else:
            event_id = request.POST.get('event_id')
            event = Event.objects.get(id=event_id)
            dts = 0
            dte = dt
            if not resize:
                event.start += dt
                dts = dt
            event.end = event.end + dt
            if CHECK_EVENT_PERM_FUNC(event, request.user):
                event.save()
                event.occurrence_set.all().update(
                    original_start=F('original_start') + dts,
                    original_end=F('original_end') + dte,
                )
                resp['status'] = "OK"
    return HttpResponse(json.dumps(resp))

@check_calendar_permissions
def api_select_create(request):
    if request.method == 'POST':
        calendar_slug = request.POST.get('calendar_slug')
        start = dateutil.parser.parse(request.POST.get('start'))
        end = dateutil.parser.parse(request.POST.get('end'))

        calendar = Calendar.objects.get(slug=calendar_slug)
        event = Event.objects.create(
                                        start=start,
                                        end=end,
                                        title=EVENT_NAME_PLACEHOLDER,
                                        calendar=calendar,
                                    )

        resp = {}
        resp['status'] = "OK"

    return HttpResponse(json.dumps(resp))
