from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.create_update import delete_object
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.views.generic.create_update import delete_object
from django.conf import settings
import datetime

from schedule.forms import EventForm
from schedule.models import *
from schedule.periods import weekday_names

def calendar_detail(request, calendar_slug, template='schedule/calendar.html',
    periods=None):
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    return render_to_response(template, {
        "calendar": calendar,
        "day_names": weekday_names,
    }, context_instance=RequestContext(request))

def calendar_by_periods(request, calendar, periods=None):
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    
    date = get_date_info(request.GET)
        try:
            date = datetime.datetime(get_date_info(request.GET))
        except ValueError:
            raise Http404
    else:
        date = datetime.datetime.now()
    period_objects = dict([period.__name__, period(calendar.events.all(), date) for period in periods])
    context = {
        'year': date.year
        'month': date.month
        'day': date.day
        'hour': date.hour
        'minute': date.minute
        'periods': period_objects
        'calendar': calendar
    }

def event(request, event_id=None):
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

def occurrence(request, event_id, occurrence_id=None):
    if(occurrence_id):
        occurrence = get_object_or_404(Occurrence, id=occurrence_id)
        event = occurrence.event
    elif(all(year, month, day, hour, minute, second)):
        event = get_object_or_404(Event, id=event_id)
        occurrence = event.get_occurrence(
            datetime.datetime(year, month, day, hour, minute, second))
    return render_to_response('schedule/event.html', {
        'event': event
        'occurrence': occurrence
    }, context_instance=RequestContext(request))
    

@login_required
def create_or_edit_event(request, calendar_id=None, event_id=None, redirect=None):
    """
    This function, if it receives a GET request or if given an invalid form in a
    POST request it will generate the following response

    * Template: schedule/create_event.html
    * Context:
        * form: an instance of EventForm
        * calendar: a Calendar with id=calendar_id

    If this form receives an event_id it will edit the event with that id, if it
    recieves a calendar_id and it is creating a new event it will add that event
    to the calendar with the id calendar_id

    If it is given a valid form in a POST request it will redirect with one of
    three options, in this order

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    instance = None
    if event_id:
        instance = get_object_or_404(Event, id=event_id)
    calendar = None
    if calendar_id is not None:
        calendar = get_object_or_404(Calendar, id=calendar_id)
    form = EventForm(data=request.POST or None, instance=instance, hour24=True)
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

@login_required
def create_event(request, calendar_id=None, calendar_slug=None, year=None, month=None, day=None, hour=None, minute=None, redirect=None):
    if calendar_id:
        calendar = get_object_or_404(Calendar, id=calendar_id)
    elif calendar_slug:
        calendar = get_object_or_404(Calendar, slug=calendar_slug)
    starttime = datetime.datetime(year=int(year),month=int(month),day=int(day),hour=int(hour),minute=int(minute))
    endtime = starttime + datetime.timedelta(minutes=30)
    end_recur = endtime + datetime.timedelta(days=8)
    init_values = {
        'start' : starttime,
        'end' : endtime,
        'end_recurring_period' : end_recur
    }
    form = EventForm(data=request.POST or None, initial=init_values)
    if form.is_valid():
        event = form.save(commit=False)
        event.creator = request.user
        event.save()
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
    
def get_date_information