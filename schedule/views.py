import datetime
from urllib.parse import quote

import dateutil.parser
import pytz
from django.conf import settings
from django.db.models import F, Q
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

try:
    from django.utils.http import url_has_allowed_host_and_scheme
except ImportError:
    # Django<=2.2
    from django.utils.http import is_safe_url as url_has_allowed_host_and_scheme

from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import (
    CreateView,
    DeleteView,
    ModelFormMixin,
    ProcessFormView,
    UpdateView,
)

from schedule.forms import EventForm, OccurrenceForm
from schedule.models import Calendar, Event, Occurrence
from schedule.periods import weekday_names
from schedule.settings import (
    CHECK_EVENT_PERM_FUNC,
    CHECK_OCCURRENCE_PERM_FUNC,
    EVENT_NAME_PLACEHOLDER,
    GET_EVENTS_FUNC,
    OCCURRENCE_CANCEL_REDIRECT,
    USE_FULLCALENDAR,
)
from schedule.utils import (
    check_calendar_permissions,
    check_event_permissions,
    check_occurrence_permissions,
    coerce_date_dict,
)


class CalendarViewPermissionMixin:
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return check_calendar_permissions(view)


class EventEditPermissionMixin:
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return check_event_permissions(view)


class OccurrenceEditPermissionMixin:
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return check_occurrence_permissions(view)


class CancelButtonMixin:
    def post(self, request, *args, **kwargs):
        next_url = kwargs.get("next")
        self.success_url = get_next_url(request, next_url)
        if "cancel" in request.POST:
            return HttpResponseRedirect(self.success_url)
        else:
            return super().post(request, *args, **kwargs)


class CalendarMixin(CalendarViewPermissionMixin):
    model = Calendar
    slug_url_kwarg = "calendar_slug"


class CalendarView(CalendarMixin, DetailView):
    template_name = "schedule/calendar.html"


class FullCalendarView(CalendarMixin, DetailView):
    template_name = "fullcalendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["calendar_slug"] = self.kwargs.get("calendar_slug")
        return context


class CalendarByPeriodsView(CalendarMixin, DetailView):
    template_name = "schedule/calendar_by_period.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        period_class = self.kwargs["period"]
        try:
            date = coerce_date_dict(self.request.GET)
        except ValueError:
            raise Http404
        if date:
            try:
                date = datetime.datetime(**date)
            except ValueError:
                raise Http404
        else:
            date = timezone.now()
        event_list = GET_EVENTS_FUNC(self.request, calendar)

        local_timezone = timezone.get_current_timezone()
        period = period_class(event_list, date, tzinfo=local_timezone)

        context.update(
            {
                "date": date,
                "period": period,
                "calendar": calendar,
                "weekday_names": weekday_names,
                "here": quote(self.request.get_full_path()),
            }
        )
        return context


class OccurrenceMixin(CalendarViewPermissionMixin, TemplateResponseMixin):
    model = Occurrence
    pk_url_kwarg = "occurrence_id"
    form_class = OccurrenceForm


class OccurrenceEditMixin(
    CancelButtonMixin, OccurrenceEditPermissionMixin, OccurrenceMixin
):
    def get_initial(self):
        initial_data = super().get_initial()
        _, self.object = get_occurrence(**self.kwargs)
        return initial_data


class OccurrenceView(OccurrenceMixin, DetailView):
    template_name = "schedule/occurrence.html"


class OccurrencePreview(OccurrenceMixin, ModelFormMixin, ProcessFormView):
    template_name = "schedule/occurrence.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context = {"event": self.object.event, "occurrence": self.object}
        return context


class EditOccurrenceView(OccurrenceEditMixin, UpdateView):
    template_name = "schedule/edit_occurrence.html"


class CreateOccurrenceView(OccurrenceEditMixin, CreateView):
    template_name = "schedule/edit_occurrence.html"


class CancelOccurrenceView(OccurrenceEditMixin, ModelFormMixin, ProcessFormView):
    template_name = "schedule/cancel_occurrence.html"

    def post(self, request, *args, **kwargs):
        event, occurrence = get_occurrence(**kwargs)
        self.success_url = kwargs.get(
            "next", get_next_url(request, event.get_absolute_url())
        )
        if "cancel" not in request.POST:
            occurrence.cancel()
        return HttpResponseRedirect(self.success_url)


class EventMixin(CalendarViewPermissionMixin):
    model = Event
    pk_url_kwarg = "event_id"


class EventEditMixin(CancelButtonMixin, EventEditPermissionMixin, EventMixin):
    pass


class EventView(EventMixin, DetailView):
    template_name = "schedule/event.html"


class EditEventView(EventEditMixin, UpdateView):
    form_class = EventForm
    template_name = "schedule/create_event.html"

    def form_valid(self, form):
        event = form.save(commit=False)
        old_event = Event.objects.get(pk=event.pk)
        dts = datetime.timedelta(
            minutes=int((event.start - old_event.start).total_seconds() / 60)
        )
        dte = datetime.timedelta(
            minutes=int((event.end - old_event.end).total_seconds() / 60)
        )
        event.occurrence_set.all().update(
            original_start=F("original_start") + dts,
            original_end=F("original_end") + dte,
        )
        event.save()
        return super().form_valid(form)


class CreateEventView(EventEditMixin, CreateView):
    form_class = EventForm
    template_name = "schedule/create_event.html"

    def get_initial(self):
        date = coerce_date_dict(self.request.GET)
        initial_data = None
        if date:
            try:
                start = datetime.datetime(**date)
                initial_data = {
                    "start": start,
                    "end": start + datetime.timedelta(minutes=30),
                }
            except TypeError:
                raise Http404
            except ValueError:
                raise Http404
        return initial_data

    def form_valid(self, form):
        event = form.save(commit=False)
        event.creator = self.request.user
        event.calendar = get_object_or_404(Calendar, slug=self.kwargs["calendar_slug"])
        event.save()
        return HttpResponseRedirect(event.get_absolute_url())


class DeleteEventView(EventEditMixin, DeleteView):
    template_name = "schedule/delete_event.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["next"] = self.get_success_url()
        return ctx

    def get_success_url(self):
        """
        After the event is deleted there are three options for redirect, tried in
        this order:
        # Try to find a 'next' GET variable
        # If the key word argument redirect is set
        # Lastly redirect to the event detail of the recently create event
        """
        url_val = "fullcalendar" if USE_FULLCALENDAR else "day_calendar"
        next_url = self.kwargs.get("next") or reverse(
            url_val, args=[self.object.calendar.slug]
        )
        next_url = get_next_url(self.request, next_url)
        return next_url


def get_occurrence(
    event_id,
    occurrence_id=None,
    year=None,
    month=None,
    day=None,
    hour=None,
    minute=None,
    second=None,
    tzinfo=None,
):
    """
    Because occurrences don't have to be persisted, there must be two ways to
    retrieve them. both need an event, but if its persisted the occurrence can
    be retrieved with an id. If it is not persisted it takes a date to
    retrieve it.  This function returns an event and occurrence regardless of
    which method is used.
    """
    if occurrence_id:
        occurrence = get_object_or_404(Occurrence, id=occurrence_id)
        event = occurrence.event
    elif None not in (year, month, day, hour, minute, second):
        event = get_object_or_404(Event, id=event_id)
        date = timezone.make_aware(
            datetime.datetime(
                int(year), int(month), int(day), int(hour), int(minute), int(second)
            ),
            tzinfo,
        )
        occurrence = event.get_occurrence(date)
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
    if not next_url or "://" in next_url:
        return None
    return next_url


def get_next_url(request, default):
    next_url = default
    if OCCURRENCE_CANCEL_REDIRECT:
        next_url = OCCURRENCE_CANCEL_REDIRECT
    _next_url = (
        request.GET.get("next")
        if request.method in ["GET", "HEAD"]
        else request.POST.get("next")
    )
    if _next_url and url_has_allowed_host_and_scheme(_next_url, request.get_host()):
        next_url = _next_url
    return next_url


@check_calendar_permissions
def api_occurrences(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    calendar_slug = request.GET.get("calendar_slug")
    timezone = request.GET.get("timezone")

    try:
        response_data = _api_occurrences(start, end, calendar_slug, timezone)
    except (ValueError, Calendar.DoesNotExist) as e:
        return HttpResponseBadRequest(e)

    return JsonResponse(response_data, safe=False)


def _api_occurrences(start, end, calendar_slug, timezone):

    if not start or not end:
        raise ValueError("Start and end parameters are required")
    # version 2 of full calendar
    # TODO: improve this code with date util package
    if "-" in start:

        def convert(ddatetime):
            if ddatetime:
                ddatetime = ddatetime.split(" ")[0]
                try:
                    return datetime.datetime.strptime(ddatetime, "%Y-%m-%d")
                except ValueError:
                    # try a different date string format first before failing
                    return datetime.datetime.strptime(ddatetime, "%Y-%m-%dT%H:%M:%S")

    else:

        def convert(ddatetime):
            return datetime.datetime.utcfromtimestamp(float(ddatetime))

    start = convert(start)
    end = convert(end)
    current_tz = False
    if timezone and timezone in pytz.common_timezones:
        # make start and end dates aware in given timezone
        current_tz = pytz.timezone(timezone)
        start = current_tz.localize(start)
        end = current_tz.localize(end)
    elif settings.USE_TZ:
        # If USE_TZ is True, make start and end dates aware in UTC timezone
        utc = pytz.UTC
        start = utc.localize(start)
        end = utc.localize(end)

    if calendar_slug:
        # will raise DoesNotExist exception if no match
        calendars = [Calendar.objects.get(slug=calendar_slug)]
    # if no calendar slug is given, get all the calendars
    else:
        calendars = Calendar.objects.all()
    response_data = []
    # Algorithm to get an id for the occurrences in fullcalendar (NOT THE SAME
    # AS IN THE DB) which are always unique.
    # Fullcalendar thinks that all their "events" with the same "event.id" in
    # their system are the same object, because it's not really built around
    # the idea of events (generators)
    # and occurrences (their events).
    # Check the "persisted" boolean value that tells it whether to change the
    # event, using the "event_id" or the occurrence with the specified "id".
    # for more info https://github.com/llazzaro/django-scheduler/pull/169
    i = 1
    if Occurrence.objects.all().exists():
        i = Occurrence.objects.latest("id").id + 1
    event_list = []
    for calendar in calendars:
        # create flat list of events from each calendar
        event_list += calendar.events.filter(start__lte=end).filter(
            Q(end_recurring_period__gte=start) | Q(end_recurring_period__isnull=True)
        )
    for event in event_list:
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            occurrence_id = i + occurrence.event.id
            existed = False

            if occurrence.id:
                occurrence_id = occurrence.id
                existed = True

            recur_rule = occurrence.event.rule.name if occurrence.event.rule else None

            if occurrence.event.end_recurring_period:
                recur_period_end = occurrence.event.end_recurring_period
                if current_tz:
                    # make recur_period_end aware in given timezone
                    recur_period_end = recur_period_end.astimezone(current_tz)
                recur_period_end = recur_period_end
            else:
                recur_period_end = None

            event_start = occurrence.start
            event_end = occurrence.end
            if current_tz:
                # make event start and end dates aware in given timezone
                event_start = event_start.astimezone(current_tz)
                event_end = event_end.astimezone(current_tz)
            if occurrence.cancelled:
                # fixes bug 508
                continue
            response_data.append(
                {
                    "id": occurrence_id,
                    "title": occurrence.title,
                    "start": event_start,
                    "end": event_end,
                    "existed": existed,
                    "event_id": occurrence.event.id,
                    "color": occurrence.event.color_event,
                    "description": occurrence.description,
                    "rule": recur_rule,
                    "end_recurring_period": recur_period_end,
                    "creator": str(occurrence.event.creator),
                    "calendar": occurrence.event.calendar.slug,
                    "cancelled": occurrence.cancelled,
                }
            )
    return response_data


@require_POST
@check_calendar_permissions
def api_move_or_resize_by_code(request):
    response_data = {}
    user = request.user
    id = request.POST.get("id")
    existed = bool(request.POST.get("existed") == "true")
    delta = datetime.timedelta(minutes=int(request.POST.get("delta")))
    resize = bool(request.POST.get("resize", False))
    event_id = request.POST.get("event_id")

    response_data = _api_move_or_resize_by_code(
        user, id, existed, delta, resize, event_id
    )

    return JsonResponse(response_data)


def _api_move_or_resize_by_code(user, id, existed, delta, resize, event_id):
    response_data = {}
    response_data["status"] = "PERMISSION DENIED"

    if existed:
        occurrence = Occurrence.objects.get(id=id)
        occurrence.end += delta
        if not resize:
            occurrence.start += delta
        if CHECK_OCCURRENCE_PERM_FUNC(occurrence, user):
            occurrence.save()
            response_data["status"] = "OK"
    else:
        event = Event.objects.get(id=event_id)
        dts = 0
        dte = delta
        if not resize:
            event.start += delta
            dts = delta
        event.end = event.end + delta
        if CHECK_EVENT_PERM_FUNC(event, user):
            event.save()
            event.occurrence_set.all().update(
                original_start=F("original_start") + dts,
                original_end=F("original_end") + dte,
            )
            response_data["status"] = "OK"
    return response_data


@require_POST
@check_calendar_permissions
def api_select_create(request):
    response_data = {}
    start = request.POST.get("start")
    end = request.POST.get("end")
    calendar_slug = request.POST.get("calendar_slug")

    response_data = _api_select_create(start, end, calendar_slug)

    return JsonResponse(response_data)


def _api_select_create(start, end, calendar_slug):
    start = dateutil.parser.parse(start)
    end = dateutil.parser.parse(end)

    calendar = Calendar.objects.get(slug=calendar_slug)
    Event.objects.create(
        start=start, end=end, title=EVENT_NAME_PLACEHOLDER, calendar=calendar
    )

    response_data = {}
    response_data["status"] = "OK"
    return response_data
