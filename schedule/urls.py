from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^calendar/(\d+)/$', 'schedule.views.calendar', name="s_calendar"),
    url(r'^calendar/(\d+)/(\d+)/(\d+)/$', 
         'schedule.views.calendar', name = "s_calendar_date"),
    url(r'^calendar/(\d+)/create_event/$', 'schedule.views.create_or_edit_event', name="s_cal_create_event"),
    url(r'^event/create/$', 'schedule.views.create_or_edit_event', name='s_create_event'),
    url(r'^event/edit/(?P<event_id>\d+)/$', 'schedule.views.create_or_edit_event', name='s_edit_event'),
    url(r'^event/(\d+)/$', 'schedule.views.event', name="s_event"),
    url(r'^event/delete/(\d+)/$', 'schedule.views.delete_event', name="s_delete_event"),
    )