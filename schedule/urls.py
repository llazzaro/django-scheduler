from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list
from schedule.models import Calendar
from schedule.feeds import UpcomingEventsFeed
from schedule.feeds import CalendarICalendar

info_dict = {
    'queryset': Calendar.objects.all(),
}

urlpatterns = patterns('',
# urls for Calendars
url(r'^calendar/year/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar', 
    name="year_calendar_date"),
url(r'^calendar/tri_month/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar', 
    name="tri_month_calendar_date"),
url(r'^calendar/compact_month/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar', 
    name = "c_calendar_date"),
url(r'^calendar/month/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar', 
    name = "m_calendar_date"),
url(r'^calendar/week/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar', 
    name = "w_calendar_date"),
url(r'^calendar/daily/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar', 
    name = "d_calendar_date"),
url(r'^calendar/(?P<calendar_slug>[-\w]+)/$', 
    'schedule.views.calendar_detail', 
    name = "s_calendar_date"),

#Event Urls
url(r'^event/create/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.create_event',
    name='s_create_event_date'),
url(r'^event/create/$', 
    'schedule.views.create_or_edit_event', 
    name='s_create_event'),
url(r'^event/edit/(?P<event_id>\d+)/$',
    'schedule.views.create_or_edit_event',
    name='s_edit_event'),
url(r'^event/(?P<event_id>\d+)/$',
    'schedule.views.event',
    name="s_event"), 
url(r'^event/delete/(?P<event_id>\d+)/$',
    'schedule.views.delete_event',
    name="s_delete_event"),

#urls for already persisted occurrences
url(r'^occurrence/(?P<occurrence_id>\d+)/$',
    'schedule.views.occurrence',
    name="s_occurrence"), 
url(r'^occurrence/cancel/(?P<occurrnece_id>\d+)/$',
    'schedule.views.cancel_occurrence',
    name="s_delete_event"),

#urls for unpersisted occurrences
url(r'^occurrence/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
    'schedule.views.occurrence', 
    name="s_occurrence_by_date"),
url(r'^occurrence/cancel/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
    'schedule.views.cancel_occurrence', 
    name="s_cancel_occurrence_by_date"),
    

#feed urls 
url(r'^feed/calendar/(.*)/$',
'django.contrib.syndication.views.feed', { "feed_dict": { "upcoming":
UpcomingEventsFeed } }), (r'^ical/calendar/(.*)/$', CalendarICalendar()),

 url(r'$', object_list, info_dict, name='schedule'), )
)