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
from django.views.generic.edit import DeleteView
from django.views.generic import UpdateView, CreateView

from schedule.conf.settings import GET_EVENTS_FUNC, OCCURRENCE_CANCEL_REDIRECT
from schedule.forms import EventForm, OccurrenceForm
from schedule.models import Calendar, Occurrence, Event
from schedule.periods import weekday_names
from schedule.utils import check_event_permissions, check_calendar_permissions, coerce_date_dict

@check_calendar_permissions
def calendar(request, calendar_slug, template='schedule/calendar.html'):
    """
    This view returns a calendar.  This view should be used if you are
    interested in the meta data of a calendar, not if you want to display a
    calendar.  It is suggested that you use calendar_by_periods if you would
    like to display a   calendar.

    Context Variables:

    ``calendar``
        The Calendar object designated by the ``calendar_slug``.
    """
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    return render_to_response(template, {
        "calendar": calendar,
    }, context_instance=RequestContext(request))

@check_calendar_permissions
def calendar_by_periods(request, calendar_slug, periods=None, template_name="schedule/calendar_by_period.html"):
    """
    This view is for getting a calendar, but also getting periods with that
    calendar.  Which periods you get, is designated with the list periods. You
    can designate which date you the periods to be initialized to by passing
    a date in request.GET. See the template tag ``query_string_for_date``

    Context Variables

    ``date``
        This was the date that was generated from the query string.

    ``periods``
        this is a dictionary that returns the periods from the list you passed
        in.  If you passed in Month and Day, then your dictionary would look
        like this

        {
            'month': <schedule.periods.Month object>
            'day':   <schedule.periods.Day object>
        }

        So in the template to access the Day period in the context you simply
        use ``periods.day``.

    ``calendar``
        This is the Calendar that is designated by the ``calendar_slug``.

    ``weekday_names``
        This is for convenience. It returns the local names of weekedays for
        internationalization.

    """
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
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

    if 'django_timezone' in request.session:
        local_timezone = pytz.timezone(request.session['django_timezone'])
    else:
        local_timezone = timezone.get_default_timezone()
    period_objects = {} 
    for period in periods:
        if period.__name__.lower() == 'year':
            period_objects[period.__name__.lower()] = period(event_list, date, None, local_timezone) 
        else:
            period_objects[period.__name__.lower()] = period(event_list, date, None, None, local_timezone)
    return render_to_response(template_name, {
        'date': date,
        'periods': period_objects,
        'calendar': calendar,
        'weekday_names': weekday_names,
        'here': quote(request.get_full_path()),
    }, context_instance=RequestContext(request), )


def event(request, event_id, template_name="schedule/event.html"):
    """
    This view is for showing an event. It is important to remember that an
    event is not an occurrence.  Events define a set of reccurring occurrences.
    If you would like to display an occurrence (a single instance of a
    recurring event) use occurrence.

    Context Variables:

    event
        This is the event designated by the event_id

    back_url
        this is the url that referred to this view.
    """
    event = get_object_or_404(Event, id=event_id)
    return render(request, template_name, {
        "event": event,
        "back_url": None,
    })


def occurrence(request, event_id, template_name="schedule/occurrence.html", *args, **kwargs):
    """
    This view is used to display an occurrence.

    Context Variables:

    ``event``
        the event that produces the occurrence

    ``occurrence``
        the occurrence to be displayed

    ``back_url``
        the url from which this request was refered
    """
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    back_url = request.META.get('HTTP_REFERER', None)
    return render_to_response(template_name, {
        'event': event,
        'occurrence': occurrence,
        'back_url': back_url,
    }, context_instance=RequestContext(request))

@check_event_permissions
def edit_occurrence(request, event_id, template_name="schedule/edit_occurrence.html", *args, **kwargs):
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next', None)
    form = OccurrenceForm(data=request.POST or None, instance=occurrence)
    if form.is_valid():
        occurrence = form.save(commit=False)
        occurrence.event = event
        occurrence.save()
        next = next or get_next_url(request, occurrence.get_absolute_url())
        return HttpResponseRedirect(next)
    next = next or get_next_url(request, occurrence.get_absolute_url())
    return render_to_response(template_name, {
        'form': form,
        'occurrence': occurrence,
        'next': next,
    }, context_instance=RequestContext(request))


@check_event_permissions
def cancel_occurrence(request, event_id, template_name='schedule/cancel_occurrence.html', *args, **kwargs):
    """
    This view is used to cancel an occurrence. If it is called with a POST it
    will cancel the view. If it is called with a GET it will ask for
    conformation to cancel.
    """
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next', None) or get_next_url(request, event.get_absolute_url())
    if request.method != "POST":
        return render_to_response(template_name, {
            "occurrence": occurrence,
            "next": next,
        }, context_instance=RequestContext(request))
    occurrence.cancel()
    return HttpResponseRedirect(next)


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

class EventMixin(object):
    def get_success_url(self):
        """
        After the event is deleted there are three options for redirect, tried in
        this order:

        # Try to find a 'next' GET variable
        # If the key word argument redirect is set
        # Lastly redirect to the event detail of the recently create event
        """
        cal_slug = self.kwargs['calendar_slug']
        if self.object:
            cal_slug = self.object.calendar.slug
        next = self.kwargs.get('next') or reverse('day_calendar', args=[cal_slug])
        next = get_next_url(self.request, next)
        return next

class EditEventView(EventMixin, UpdateView):
    model = Event
    pk_url_kwarg = 'event_id'
    form_class = EventForm
    template_name = 'schedule/create_event.html'

    def get_object(self):
        return get_object_or_404(Event, id=self.kwargs['event_id'])

    def get_context_data(self, **kwargs):
        ctx = super(EditEventView, self).get_context_data(**kwargs)
        ctx['next'] = self.get_success_url()
        return ctx

    @method_decorator(login_required)
    @method_decorator(check_event_permissions)
    def dispatch(self, *args, **kwargs): 
        self.event_id = kwargs['event_id'] 
        return super(EditEventView, self).dispatch(*args, **kwargs) 

    #def form_valid(self, form): 
    #    event = form.save(commit=False)
    #    event.save()
    #    next = None or reverse('event', args=[event.id])
    #    next = get_next_url(self.request, next)
    #    return HttpResponseRedirect(next)

class CreateEventView(EventMixin, CreateView):
    model = Event
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

    def get_context_data(self, **kwargs):
        ctx = super(CreateEventView, self).get_context_data(**kwargs)
        ctx['next'] = self.get_success_url()
        return ctx

    @method_decorator(login_required)
    @method_decorator(check_event_permissions)
    def dispatch(self, *args, **kwargs): 
        return super(CreateEventView, self).dispatch(*args, **kwargs) 

    def form_valid(self, form): 
        event = form.save(commit=False)
        event.creator = self.request.user
        event.calendar = get_object_or_404(Calendar, slug=self.kwargs['calendar_slug'])
        event.save()
        next = None or reverse('event', args=[event.id])
        next = get_next_url(self.request, next)
        return HttpResponseRedirect(next)

class DeleteEventView(EventMixin, DeleteView):
    template_name = 'schedule/delete_event.html'
    pk_url_kwarg = 'event_id'
    model = Event

    def get_context_data(self, **kwargs):
        ctx = super(DeleteEventView, self).get_context_data(**kwargs)
        ctx['next'] = self.get_success_url()
        return ctx

    ## Override dispatch to apply the permission decorator
    @method_decorator(login_required)
    @method_decorator(check_event_permissions)
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteEventView, self).dispatch(request, *args, **kwargs)


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
