from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list
from schedule.models import Calendar
from schedule.feeds import UpcomingEventsFeed
from schedule.feeds import CalendarICalendar
from schedule.periods import Year, Month, Week, Day

info_dict = {
    'queryset': Calendar.objects.all(),
}

urlpatterns = patterns('',

# urls for Calendars
url(r'^calendar/$',
    object_list,
    name="schedule",
    kwargs={'queryset':Calendar.objects.all(), 'template_name':'schedule/calendar_list.html'}),

url(r'^calendar/year/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name="year_calendar",
    kwargs={'periods': [Year], 'template_name': 'schedule/calendar_year.html'}),

url(r'^calendar/tri_month/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name="tri_month_calendar",
    kwargs={'periods': [Month], 'template_name': 'schedule/calendar_tri_month.html'}),

url(r'^calendar/compact_month/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name = "compact_calendar",
    kwargs={'periods': [Month], 'template_name': 'schedule/calendar_compact_month.html'}),

url(r'^calendar/month/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name = "month_calendar",
    kwargs={'periods': [Month], 'template_name': 'schedule/calendar_month.html'}),

url(r'^calendar/week/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name = "week_calendar",
    kwargs={'periods': [Week], 'template_name': 'schedule/calendar_week.html'}),

url(r'^calendar/daily/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar_by_periods',
    name = "day_calendar",
    kwargs={'periods': [Day], 'template_name': 'schedule/calendar_day.html'}),

url(r'^calendar/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.calendar',
    name = "calendar_home",
    ),

#Event Urls
url(r'^event/create/(?P<calendar_slug>[-\w]+)/$',
    'schedule.views.create_or_edit_event',
    name='calendar_create_event'),
url(r'^event/edit/(?P<calendar_slug>[-\w]+)/(?P<event_id>\d+)/$',
    'schedule.views.create_or_edit_event',
    name='edit_event'),
url(r'^event/(?P<event_id>\d+)/$',
    'schedule.views.event',
    name="event"), 
url(r'^event/delete/(?P<event_id>\d+)/$',
    'schedule.views.delete_event',
    name="delete_event"),

#urls for already persisted occurrences
url(r'^occurrence/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
    'schedule.views.occurrence',
    name="occurrence"), 
url(r'^occurrence/cancel/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
    'schedule.views.cancel_occurrence',
    name="cancel_occurrence"),
url(r'^occurrence/edit/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
    'schedule.views.edit_occurrence',
    name="edit_occurrence"),

#urls for unpersisted occurrences
url(r'^occurrence/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
    'schedule.views.occurrence', 
    name="occurrence_by_date"),
url(r'^occurrence/cancel/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
    'schedule.views.cancel_occurrence', 
    name="cancel_occurrence_by_date"),
url(r'^occurrence/edit/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
    'schedule.views.edit_occurrence', 
    name="edit_occurrence_by_date"),
    

#feed urls 
url(r'^feed/calendar/(.*)/$',
    'django.contrib.syndication.views.feed', 
    { "feed_dict": { "upcoming": UpcomingEventsFeed } }),
 
(r'^ical/calendar/(.*)/$', CalendarICalendar()),

 url(r'$', object_list, info_dict, name='schedule'), 
)
