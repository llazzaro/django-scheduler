from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^calendar/(?P<calendar_id>\d+)/$', 'schedule.views.calendar', name="s_calendar"),
    url(r'^calendar/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$',
         'schedule.views.calendar', name = "s_calendar_date"),
    url(r'^calendar/(?P<calendar_id>\d+)/create_event/$', 'schedule.views.create_or_edit_event', name="s_create_event_in_calendar"),
    url(r'^event/create/$', 'schedule.views.create_or_edit_event', name='s_create_event'),
    url(r'^event/edit/(?P<event_id>\d+)/$', 'schedule.views.create_or_edit_event', name='s_edit_event'),
    url(r'^event/(?P<event_id>\d+)/$', 'schedule.views.event', name="s_event"),
    url(r'^event/delete/(?P<event_id>\d+)/$', 'schedule.views.delete_event', name="s_delete_event"),
    )
