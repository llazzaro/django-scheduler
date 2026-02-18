import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo, available_timezones

import dateutil.parser
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
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
from schedule.models import Calendar, Event, Occurrence, Rule, RuleParam
from schedule.periods import Period, weekday_names
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
        context = super().get_context_data(**kwargs)
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

    @property
    def date_from_url(self):
        return datetime.datetime(
            int(self.kwargs["year"]),
            int(self.kwargs["month"]),
            int(self.kwargs["day"]),
            int(self.kwargs["hour"]),
            int(self.kwargs["minute"]),
            int(self.kwargs["second"]),
            tzinfo=datetime.timezone.utc,
        )

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, pk=self.kwargs["event_id"])
        period = Period(
            [event],
            start=self.date_from_url,
            end=self.date_from_url,
        )

        try:
            return period.get_occurrences()[0]
        except IndexError:
            raise Http404

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"event": self.object.event, "occurrence": self.object})
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
        with transaction.atomic():
            event = form.save(commit=False)
            old_event = Event.objects.select_for_update().get(pk=event.pk)
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
            event.updater = self.request.user
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
        date = datetime.datetime(
            int(year), int(month), int(day), int(hour), int(minute), int(second)
        )
        if settings.USE_TZ:
            date = timezone.make_aware(date, tzinfo)
        elif tzinfo is not None:
            # USE_TZ=False: wall-clock values are in the given timezone;
            # convert to server time (naive) for DB compatibility.
            server_tz = ZoneInfo(settings.TIME_ZONE)
            date = (
                date.replace(tzinfo=tzinfo).astimezone(server_tz).replace(tzinfo=None)
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


def drfize(f):
    """Given F, wrap it in a rest framework API, require authentication and requires POST"""
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated

    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def g(*args, **kwargs):
        return f(*args, **kwargs)

    return g


@check_calendar_permissions
def api_occurrences(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    timezone = request.GET.get("timezone")

    calendar_slugs_raw = request.GET.get("calendar_slug")
    calendar_slugs = calendar_slugs_raw.split(",") if calendar_slugs_raw else []

    try:
        response_data = _api_occurrences(start, end, calendar_slugs, timezone)
    except (ValueError, Calendar.DoesNotExist) as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse(response_data, safe=False)


def _api_occurrences(start, end, calendar_slugs, timezone):
    if not start or not end:
        raise ValueError("Start and end parameters are required")
    # version 2 of full calendar
    if "-" in start:

        def convert(ddatetime):
            if ddatetime:
                return dateutil.parser.parse(ddatetime)

    else:

        def convert(ddatetime):
            return datetime.datetime.fromtimestamp(
                float(ddatetime), tz=datetime.timezone.utc
            )

    start = convert(start)
    end = convert(end)
    current_tz = False
    if timezone and timezone in available_timezones():
        # make start and end dates aware in given timezone
        current_tz = ZoneInfo(timezone)
        if start.tzinfo is not None:
            start = start.astimezone(current_tz)
        else:
            start = start.replace(tzinfo=current_tz)
        if end.tzinfo is not None:
            end = end.astimezone(current_tz)
        else:
            end = end.replace(tzinfo=current_tz)
    elif settings.USE_TZ:
        # If USE_TZ is True, make start and end dates aware in UTC timezone
        utc = datetime.timezone.utc
        if start.tzinfo is not None:
            start = start.astimezone(utc)
        else:
            start = start.replace(tzinfo=utc)
        if end.tzinfo is not None:
            end = end.astimezone(utc)
        else:
            end = end.replace(tzinfo=utc)

    # When USE_TZ=False, the model layer expects naive server-time datetimes.
    # Ensure start/end are naive, even if they came in as aware (e.g. float
    # timestamps or an explicit timezone parameter).
    if not settings.USE_TZ:
        _server_tz = ZoneInfo(settings.TIME_ZONE)
        if start.tzinfo is not None:
            start = start.astimezone(_server_tz).replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.astimezone(_server_tz).replace(tzinfo=None)

    if calendar_slugs:
        # will raise DoesNotExist exception if no match
        calendars = list(Calendar.objects.filter(slug__in=calendar_slugs))
        missing_calendars = set(calendar_slugs) - set([s.slug for s in calendars])
        if missing_calendars:
            missing_msg = ", ".join("'{0}'".format(s) for s in missing_calendars)
            msg = "Calendars {0} do not exist.".format(missing_msg)
            raise Calendar.DoesNotExist(msg)
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
    # Non-persisted occurrences get negative IDs so they can never collide
    # with real PKs, even across cached FullCalendar responses.
    next_temp_id = -1
    event_list = []
    for calendar in calendars:
        # create flat list of events from each calendar
        event_list += (
            calendar.events.filter(start__lte=end)
            .filter(
                Q(end_recurring_period__gte=start)
                | Q(end_recurring_period__isnull=True)
            )
            .select_related("rule")
            .prefetch_related("rule__repeats")
        )
    for event in event_list:
        occurrences = event.get_occurrences(start, end)
        for occurrence in occurrences:
            existed = False

            if occurrence.id:
                occurrence_id = occurrence.id
                existed = True
            else:
                occurrence_id = next_temp_id
                next_temp_id -= 1

            recur_rule = occurrence.event.rule.name if occurrence.event.rule else None

            if occurrence.event.end_recurring_period:
                recur_period_end = occurrence.event.end_recurring_period
                if current_tz:
                    # make recur_period_end aware in given timezone
                    if recur_period_end.tzinfo is not None:
                        recur_period_end = recur_period_end.astimezone(current_tz)
                    else:
                        recur_period_end = recur_period_end.replace(
                            tzinfo=ZoneInfo(settings.TIME_ZONE)
                        ).astimezone(current_tz)
            else:
                recur_period_end = None

            event_start = occurrence.start
            event_end = occurrence.end
            if current_tz:
                # make event start and end dates aware in given timezone
                if event_start.tzinfo is None:
                    _svr_tz = ZoneInfo(settings.TIME_ZONE)
                    event_start = event_start.replace(tzinfo=_svr_tz).astimezone(
                        current_tz
                    )
                    event_end = event_end.replace(tzinfo=_svr_tz).astimezone(current_tz)
                else:
                    event_start = event_start.astimezone(current_tz)
                    event_end = event_end.astimezone(current_tz)
            if occurrence.cancelled:
                # fixes bug 508
                continue
            if occurrence.start.tzinfo is not None:
                local_start = occurrence.start.astimezone(occurrence.event.event_tzinfo)
                local_end = occurrence.end.astimezone(occurrence.event.event_tzinfo)
            else:
                _server_tz = ZoneInfo(settings.TIME_ZONE)
                local_start = occurrence.start.replace(tzinfo=_server_tz).astimezone(
                    occurrence.event.event_tzinfo
                )
                local_end = occurrence.end.replace(tzinfo=_server_tz).astimezone(
                    occurrence.event.event_tzinfo
                )
            allDay = (
                local_start.hour == 0
                and local_start.minute == 0
                and local_start.second == 0
                and local_end.hour == 0
                and local_end.minute == 0
                and local_end.second == 0
                and (local_end - local_start).days >= 1
            )
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
                    "creator": (
                        str(occurrence.event.creator)
                        if occurrence.event.creator is not None
                        else None
                    ),
                    "calendar": occurrence.event.calendar.slug,
                    "cancelled": occurrence.cancelled,
                    "allDay": allDay,
                    "groupId": occurrence.event.id,
                    "recurrence_frequency": (
                        occurrence.event.rule.frequency
                        if occurrence.event.rule is not None
                        else None
                    ),
                    "recurrence_repeats": (
                        compress_repeats(
                            [
                                (repeat.param.name, repeat.value)
                                for repeat in occurrence.event.rule.repeats.all()
                            ]
                        )
                        if occurrence.event.rule is not None
                        else None
                    ),
                }
            )
    return response_data


@check_calendar_permissions
def api_calendars(request):
    calendars = Calendar.objects.all()
    return JsonResponse(
        {
            "status": "OK",
            "calendars": [
                {
                    "name": calendar.name,
                    "slug": calendar.slug,
                    "color_event": calendar.color_event,
                }
                for calendar in calendars
            ],
        }
    )


@drfize
@require_POST
@check_calendar_permissions
def api_move_or_resize_by_code(request):
    from rest_framework.exceptions import ValidationError as DRFValidationError

    user = request.user
    try:
        id = request.POST.get("id")
        existed = request.POST.get("existed") == "true"
        delta = datetime.timedelta(minutes=int(request.POST.get("delta")))
        resize = request.POST.get("resize") == "true"
        event_id = request.POST.get("event_id")
        calendar_slug = request.POST.get("calendar_slug")
    except (TypeError, ValueError) as e:
        raise DRFValidationError(str(e))

    try:
        response_data = _api_move_or_resize_by_code(
            user, id, existed, delta, resize, event_id, calendar_slug
        )
    except ValueError as e:
        raise DRFValidationError(str(e))
    except (Event.DoesNotExist, Occurrence.DoesNotExist):
        raise Http404

    return JsonResponse(response_data)


def _api_move_or_resize_by_code(
    user, id, existed, delta, resize, event_id, calendar_slug
):
    response_data = {}
    response_data["status"] = "PERMISSION DENIED"

    with transaction.atomic():
        if existed:
            occurrence = Occurrence.objects.select_for_update().get(id=id)
            if calendar_slug and occurrence.event.calendar.slug != calendar_slug:
                raise ValueError("Event does not belong to the specified calendar")
            occurrence.end += delta
            if not resize:
                occurrence.start += delta
            if occurrence.end < occurrence.start:
                raise ValueError("The end time must be later than start time.")
            if CHECK_OCCURRENCE_PERM_FUNC(occurrence, user):
                occurrence.save()
                response_data["status"] = "OK"
        else:
            event = Event.objects.select_for_update().get(id=event_id)
            if calendar_slug and event.calendar.slug != calendar_slug:
                raise ValueError("Event does not belong to the specified calendar")
            dts = datetime.timedelta()
            dte = delta
            if not resize:
                event.start += delta
                dts = delta
            event.end = event.end + delta
            if event.end < event.start:
                raise ValueError("The end time must be later than start time.")
            if CHECK_EVENT_PERM_FUNC(event, user):
                event.save()
                event.occurrence_set.all().update(
                    original_start=F("original_start") + dts,
                    original_end=F("original_end") + dte,
                )
                response_data["status"] = "OK"
    return response_data


def decode_recurrence_params(data):
    recurrence = {}
    for key, values in data.items():
        if key.startswith("recurrence_by"):
            key = key[len("recurrence_") :]
            if values == "":
                continue
            if key not in recurrence:
                recurrence[key] = []
            values = map(int, values.split(","))
            for value in values:
                recurrence[key].append(value)
    return recurrence


def compress_repeats(repeats):
    """Given REPEATS, a list like [("bymonthday", 1), ("bymonthday", 2)] returns {"bymonthday": [1,2]}"""
    recurrence = {}
    for name, value in repeats:
        if name not in recurrence:
            recurrence[name] = []
        recurrence[name].append(value)
    return recurrence


@drfize
@require_POST
@check_calendar_permissions
def api_select_create(request):
    from rest_framework.exceptions import ValidationError as DRFValidationError

    start = request.POST.get("start")
    end = request.POST.get("end")
    calendar_slug = request.POST.get("calendar_slug")
    title = request.POST.get("title")
    color = request.POST.get("color")
    description = request.POST.get("description")
    recurrence_frequency = request.POST.get("recurrence_frequency")

    event_timezone = request.POST.get("timezone")
    try:
        recurrence = decode_recurrence_params(request.POST)
        response_data = _api_select_create(
            start,
            end,
            calendar_slug,
            title,
            color,
            description,
            request.user,
            recurrence_frequency,
            recurrence,
            event_timezone,
        )
    except (TypeError, ValueError) as e:
        raise DRFValidationError(str(e))
    except Calendar.DoesNotExist:
        raise Http404

    return JsonResponse(response_data)


def _api_select_create(
    start,
    end,
    calendar_slug,
    title,
    color,
    description,
    creator,
    recurrence_frequency,
    recurrence,
    event_timezone=None,
):
    start = dateutil.parser.parse(start)
    end = dateutil.parser.parse(end)
    if start >= end:
        raise ValueError("The end time must be later than start time.")

    if event_timezone and event_timezone in available_timezones():
        tz_name = event_timezone
    else:
        tz_name = settings.TIME_ZONE

    calendar = Calendar.objects.get(slug=calendar_slug)
    rule = (
        Rule.ensure_rule(frequency=recurrence_frequency, by_details=recurrence)
        if recurrence_frequency
        else None
    )
    event = Event.objects.create(
        creator=creator,
        start=start,
        end=end,
        title=title or EVENT_NAME_PLACEHOLDER,
        calendar=calendar,
        color_event=color or "",
        description=description or "",
        rule=rule,
        timezone=tz_name,
    )
    response_data = {}
    response_data["status"] = "OK"
    response_data["event_id"] = event.id
    return response_data


@drfize
@require_POST
@check_calendar_permissions
def api_delete(request):
    from rest_framework.exceptions import ValidationError as DRFValidationError

    id = request.POST.get("id")
    existed = request.POST.get("existed") == "true"
    event_id = request.POST.get("event_id")
    calendar_slug = request.POST.get("calendar_slug")
    try:
        response_data = _api_delete(id, existed, event_id, calendar_slug, request.user)
    except ValueError as e:
        raise DRFValidationError(str(e))
    except (Event.DoesNotExist, Occurrence.DoesNotExist, Calendar.DoesNotExist):
        raise Http404
    return JsonResponse(response_data)


def _api_delete(id, existed, event_id, calendar_slug, user):
    response_data = {}
    response_data["status"] = "PERMISSION DENIED"
    calendar = Calendar.objects.get(slug=calendar_slug)
    with transaction.atomic():
        if existed:
            occurrence = Occurrence.objects.get(id=id)
            event = occurrence.event
            if event.calendar_id != calendar.id:
                raise ValueError("Event does not belong to the specified calendar")
            if CHECK_EVENT_PERM_FUNC(event, user):
                occurrence.delete()
                event.save()
                response_data["status"] = "OK"
        else:
            event = Event.objects.get(id=event_id)
            if event.calendar_id != calendar.id:
                raise ValueError("Event does not belong to the specified calendar")
            if CHECK_EVENT_PERM_FUNC(event, user):
                event.delete()
                response_data["status"] = "OK"

    return response_data


@drfize
@require_POST
@check_calendar_permissions
def api_set_props(request):
    from rest_framework.exceptions import ValidationError as DRFValidationError

    id = request.POST.get("id")
    existed = request.POST.get("existed") == "true"
    event_id = request.POST.get("event_id")
    calendar_slug = request.POST.get("calendar_slug")
    try:
        response_data = _api_set_props(
            id,
            existed,
            event_id,
            calendar_slug,
            dict(
                [
                    (key[len("prop_") :], value)
                    for key, value in request.POST.items()
                    if key.startswith("prop_")
                ]
            ),
            request.user,
        )
    except ValueError as e:
        raise DRFValidationError(str(e))
    except (Event.DoesNotExist, Occurrence.DoesNotExist, Calendar.DoesNotExist):
        raise Http404
    return JsonResponse(response_data)


def _api_set_props(id, existed, event_id, calendar_slug, properties, updater):
    response_data = {}
    response_data["status"] = "PERMISSION DENIED"
    calendar = Calendar.objects.get(slug=calendar_slug)

    with transaction.atomic():
        if existed:
            occurrence = Occurrence.objects.get(id=id)
            event = occurrence.event
            if event.calendar_id != calendar.id:
                raise ValueError("Event does not belong to the specified calendar")
            if not CHECK_EVENT_PERM_FUNC(event, updater):
                return response_data

            if "title" in properties:
                occurrence.title = properties["title"]
            if "description" in properties:
                occurrence.description = properties["description"] or ""
                event.description = properties["description"] or ""
            if "color" in properties:
                event.color_event = properties["color"] or ""
            if "title" in properties or "description" in properties:
                occurrence.save()
            if "color" in properties or "description" in properties:
                event.updater = updater
                event.save()
        else:
            event = Event.objects.get(id=event_id)
            if event.calendar_id != calendar.id:
                raise ValueError("Event does not belong to the specified calendar")
            if not CHECK_EVENT_PERM_FUNC(event, updater):
                return response_data
            if "title" in properties:
                event.title = properties["title"]
            if "color" in properties:
                event.color_event = properties["color"] or ""
            if "description" in properties:
                event.description = properties["description"] or ""
            if any(k in properties for k in ("title", "color", "description")):
                event.updater = updater
                event.save()
            for occurrence in event.occurrence_set.all():
                if "title" in properties:
                    occurrence.title = properties["title"]
                if "description" in properties:
                    occurrence.description = properties["description"]
                if "title" in properties or "description" in properties:
                    occurrence.save()

        if any(key for key in properties.keys() if key.startswith("recurrence_")):
            recurrence_frequency = properties.get("recurrence_frequency")
            if not recurrence_frequency:
                raise ValueError(
                    "recurrence_frequency is required when setting recurrence properties"
                )
            recurrence_end_recurring_period = (
                properties.get("recurrence_end_recurring_period") or None
            )
            recurrence = decode_recurrence_params(properties)
            rule = Rule.ensure_rule(
                frequency=recurrence_frequency, by_details=recurrence
            )
            if event.rule is None or event.rule.id != rule.id:
                response_data["recurrence_status"] = "RECREATED"
                event.rule = rule
                if recurrence_end_recurring_period:
                    event.end_recurring_period = dateutil.parser.parse(
                        recurrence_end_recurring_period
                    )
                event.save()
    response_data["status"] = "OK"
    return response_data


@check_calendar_permissions
def api_ruleparams(request):
    ruleparams = RuleParam.objects.all()
    return JsonResponse(
        {
            "status": "OK",
            "ruleparams": [
                {
                    "id": ruleparam.id,
                    "name": ruleparam.name,
                    "display_string": ruleparam.display_string,
                    "variants": [
                        {
                            "id": ruleparamvariant.id,
                            "value_display_string": ruleparamvariant.value_display_string,
                            "value": ruleparamvariant.value,
                        }
                        for ruleparamvariant in ruleparam.variant_set.all()
                    ],
                }
                for ruleparam in ruleparams.prefetch_related("variant_set")
            ],
        }
    )
