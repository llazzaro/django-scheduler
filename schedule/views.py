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
from schedule.periods import Month


def calendar(request, calendar_id=None, year=None, month=None):
    calendar = get_object_or_404(Calendar, id = calendar_id)
    if year and month:
        month = calendar.get_month(datetime.date(int(year),int(month),1))
    else:
        month = calendar.get_month()
    return render_to_response('schedule/calendar.html', {
        "calendar": calendar,
        "month": month,
    }, context_instance=RequestContext(request))

def event(request, event_id=None):
    event = get_object_or_404(Event, id=event_id)
    return render_to_response('schedule/event.html', {
        "event": event,
    }, context_instance=RequestContext(request))

@login_required
def create_or_edit_event(request, calendar_id=None, event_id=None, redirect=None):
    """
    This function, if it recieves a GET request or if given an invalid form in a
    POST request it will generate the following response

    * Template: schedule/create_event.html
    * Context:
        * form: an instance of EventForm
        * calendar: a Calendar with id=calendar_id

    If this form recieves an event_id it will edit the event with that id, if it
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
            next = _check_next_url(request.GET['next']) or next
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

def _check_next_url(next):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if '://' in next:
        return None
    return next
