from django.conf.urls import url
from django.views.generic.list import ListView
from schedule.models import Calendar
from schedule.feeds import UpcomingEventsFeed
from schedule.feeds import CalendarICalendar
from schedule.periods import Year, Month, Week, Day
from schedule.views import (
    CalendarByPeriodsView, CalendarView, EventView,
    OccurrenceView, EditOccurrenceView, DeleteEventView,
    EditEventView, CreateEventView, OccurrencePreview,
    CreateOccurrenceView, CancelOccurrenceView, FullCalendarView,
    api_select_create, api_move_or_resize_by_code, api_occurrences)

urlpatterns = [
    url(r'^$', ListView.as_view(model=Calendar), name='calendar_list'),

    url(r'^calendar/year/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_year.html'),
        name='year_calendar',
        kwargs={'period': Year}),

    url(r'^calendar/tri_month/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_tri_month.html'),
        name='tri_month_calendar',
        kwargs={'period': Month}),

    url(r'^calendar/compact_month/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_compact_month.html'),
        name='compact_calendar',
        kwargs={'period': Month}),

    url(r'^calendar/month/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_month.html'),
        name='month_calendar',
        kwargs={'period': Month}),

    url(r'^calendar/week/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_week.html'),
        name='week_calendar',
        kwargs={'period': Week}),

    url(r'^calendar/daily/(?P<calendar_slug>[-\w]+)/$',
        CalendarByPeriodsView.as_view(template_name='schedule/calendar_day.html'),
        name='day_calendar',
        kwargs={'period': Day}),

    url(r'^calendar/(?P<calendar_slug>[-\w]+)/$',
        CalendarView.as_view(),
        name='calendar_home',
        ),
    url(r'^fullcalendar/(?P<calendar_slug>[-\w]+)/$',
        FullCalendarView.as_view(),
        name='fullcalendar'),

    # Event Urls
    url(r'^event/create/(?P<calendar_slug>[-\w]+)/$',
        CreateEventView.as_view(),
        name='calendar_create_event'),
    url(r'^event/edit/(?P<calendar_slug>[-\w]+)/(?P<event_id>\d+)/$',
        EditEventView.as_view(),
        name='edit_event'),
    url(r'^event/(?P<event_id>\d+)/$',
        EventView.as_view(),
        name='event'),
    url(r'^event/delete/(?P<event_id>\d+)/$',
        DeleteEventView.as_view(),
        name='delete_event'),

    # urls for already persisted occurrences
    url(r'^occurrence/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
        OccurrenceView.as_view(),
        name='occurrence'),
    url(r'^occurrence/cancel/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
        CancelOccurrenceView.as_view(),
        name='cancel_occurrence'),
    url(r'^occurrence/edit/(?P<event_id>\d+)/(?P<occurrence_id>\d+)/$',
        EditOccurrenceView.as_view(),
        name='edit_occurrence'),

    # urls for unpersisted occurrences
    url(r'^occurrence/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
        OccurrencePreview.as_view(),
        name='occurrence_by_date'),
    url(r'^occurrence/cancel/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
        CancelOccurrenceView.as_view(),
        name='cancel_occurrence_by_date'),
    url(r'^occurrence/edit/(?P<event_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/(?P<second>\d+)/$',
        CreateOccurrenceView.as_view(),
        name='edit_occurrence_by_date'),

    # feed urls
    url(r'^feed/calendar/upcoming/(?P<calendar_id>\d+)/$', UpcomingEventsFeed(), name='upcoming_events_feed'),
    url(r'^ical/calendar/(.*)/$', CalendarICalendar(), name='calendar_ical'),

    # api urls
    url(r'^api/occurrences', api_occurrences, name='api_occurences'),
    url(r'^api/move_or_resize/$',
        api_move_or_resize_by_code,
        name='api_move_or_resize'),
    url(r'^api/select_create/$',
        api_select_create,
        name='api_select_create'),
    url(r'^$', ListView.as_view(queryset=Calendar.objects.all()), name='schedule'),
]
