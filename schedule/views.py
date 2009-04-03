from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.create_update import delete_object
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic.create_update import delete_object
from django.conf import settings
import datetime

from schedule.forms import EventForm
from schedule.models import *
from schedule.periods import weekday_names

def calendar_detail(request, calendar_slug, template='schedule/calendar.html',
    periods=None):
    """
    This view returns a calendar.  This view should be used if you are
    interested in the meta data of a calendar, not if you want to display a
    calendar.  It is suggested that you use calendar_by_periods if you would
    like to display a calendar.
    
    Context Variables:
    
    ``calendar``
        The Calendar object designated by the ``calendar_slug``.
    """
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    return render_to_response(template, {
        "calendar": calendar,
    }, context_instance=RequestContext(request))

def calendar_by_periods(request, calendar_slug, periods=None):
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
    date = coerce_date_dict(request.GET)
    if date:
        try:
            date = datetime.datetime(**date)
        except ValueError:
            raise Http404
    else:
        date = datetime.datetime.now()
    period_objects = dict([(period.__name__, period(calendar.events.all(), date)) for period in periods])
    context = {
        'date': date,
        'periods': period_objects,
        'calendar': calendar,
        'weekday_names': weekday_names,
    }

def event(request, event_id=None):
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
    
    calendar
        this is the calendar that the event is linked to.
    """
    event = get_object_or_404(Event, id=event_id)
    back_url = request.META.get('HTTP_REFERER', None)
    try:
        cal = event.calendar_set.get()
    except:
        cal = None
    return render_to_response('schedule/event.html', {
        "event": event,
        "back_url" : back_url,
        "calendar" : cal,
    }, context_instance=RequestContext(request))

def occurrence(request, *args, **kwargs):
    """
    This view is used to display an occurrence.
    
    Context Variables:
    
    ``event``
        the event that produces the occurrence
    
    ``occurrence`` the occurrence to be displayed
    """
    event, occurrence = get_occurrence(*args, **kwargs)
    return render_to_response('schedule/event.html', {
        'event': event
        'occurrence': occurrence
    }, context_instance=RequestContex(request))

# Not implemented yet
def edit_occurrence(request, *args, **kwargs):
    event, occurrence = get_occurrence(*args, **kwargs)
    raise Http404, "Not implemented yet"

def cancel_occurrence(request, *args, **kwargs):
    """
    This view is used to cancel an occurrence. If it is called with a POST it
    will cancel the view. If it is called with a GET it will ask for
    conformation to cancel.
    """
    if request.GET:
        return render_to_response(template_name)
    event, occurrence = get_occurrence(*args, **kwargs)
    occurrence.cancel()
    return HttpResponseRedirect(next)
    
    

def get_occurrence(request, event_id, occurrence_id=None, year=None, month=None,
    day=None, hour=None, minute=None, second=None):
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
    elif(all(year, month, day, hour, minute, second)):
        event = get_object_or_404(Event, id=event_id)
        occurrence = event.get_occurrence(
            datetime.datetime(year, month, day, hour, minute, second))
        if occurrence is None:
            raise 404
    else:
        raise Http404
    return event, occurrence


@login_required
def create_or_edit_event(request, calendar_id=None, event_id=None, redirect=None):
    """
    This function, if it receives a GET request or if given an invalid form in a
    POST request it will generate the following response

    Template:
        schedule/create_event.html
    
    Context Variables:
        
    form:
        an instance of EventForm
    
    calendar: 
        a Calendar with id=calendar_id

    if this function gets a GET request with ``year``, ``month``, ``day``,
    ``hour``, ``minute``, and ``second`` it will auto fill the form, with
    the date specifed in the GET being the start and 30 minutes from that
    being the end.

    If this form receives an event_id it will edit the event with that id, if it
    recieves a calendar_id and it is creating a new event it will add that event
    to the calendar with the id calendar_id

    If it is given a valid form in a POST request it will redirect with one of
    three options, in this order

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    date = coerce_date_dict(request.GET)
    inital_data = None
    if date is not None:
        try:
            initial_data = {
                "start":datetime.datetime(**date)
                "end":datetime.timedelta(minutes=30)
            }
        except ValueError:
            raise Http404
    
    instance = None
    if event_id is not None:
        instance = get_object_or_404(Event, id=event_id)
    calendar = None
    if calendar_id is not None:
        calendar = get_object_or_404(Calendar, id=calendar_id)
    
    form = EventForm(data=request.POST or None, instance=instance, 
        hour24=True, initial=initial_data)
    
    if form.is_valid():
        event = form.save(commit=False)
        if instance is None:
            event.creator = request.user
        event.save()
        if calendar is not None and instance is None:
            calendar.events.add(event)
        next = redirect or reverse('s_event', args=[event.id])
        if 'next' in request.GET:
            next = check_next_url(request.GET['next']) or next
        return HttpResponseRedirect(next)
    
    return render_to_response('schedule/create_event.html', {
        "form": form,
        "calendar": calendar
    }, context_instance=RequestContext(request))


def delete_event(request, event_id=None, redirect=None, login_required=True):
    """
    After the event is deleted there are three options for redirect, tried in
    this order:

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    next = redirect or reverse('s_create_event')
    if 'next' in request.GET:
        next = _check_next_url(request.GET['next']) or next
    return delete_object(request,
                         model = Event,
                         object_id = event_id,
                         post_delete_redirect = next,
                         template_name = "schedule/delete_event.html",
                         login_required = login_required
                        )

def check_next_url(next):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if '://' in next:
        return None
    return next
    
def coerce_date_dict(date_dict):
    """
    given a dictionary (presumed to be from request.GET) it returns a tuple 
    that represents a date. It will return from year down to seconds until one
    is not found.  ie if year, month, and seconds are in the dictionary, only 
    year and month will be returned, the rest will be returned as min. If none
    of the parts are found return an empty tuple.
    """
    keys = ['year', 'month', 'day', 'hour', 'minute', 'second']
    retVal = {
                'year': 1,
                'month': 1,
                'day': 1,
                'hour': 0,
                'minute': 0,
                'second': 0}
    modified = False
    for key in keys:
        try:
            retVal[key] = int(date_dict[key])
            modified = True
        except KeyError:
            break
    return modified and retVal or {}
