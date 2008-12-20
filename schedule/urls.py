from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list
from schedule.models import Calendar

info_dict = {
    'queryset': Calendar.objects.all(),
}

urlpatterns = patterns('',
    # By calendar_slug
    url(r'^calendar/year/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_year', name="year_calendar"),
    url(r'^calendar/year/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/$', 'schedule.views.calendar_year', name="year_calendar_date"),
    url(r'^calendar/tri_month/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_tri_month', name="tri_month_calendar"),
    url(r'^calendar/tri_month/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_tri_month', name="tri_month_calendar_date"),
    url(r'^calendar/compact_month/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_compact_month', name="c_calendar"),
    url(r'^calendar/compact_month/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_compact_month', name = "c_calendar_date"),
    url(r'^calendar/month/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_month', name="m_calendar"),
    url(r'^calendar/month/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_month', name = "m_calendar_date"),
    url(r'^calendar/week/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_week', name="w_calendar"),
    url(r'^calendar/week/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'schedule.views.calendar_week', name = "w_calendar_date"),
    url(r'^calendar/daily/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar_day', name="d_calendar"),
    url(r'^calendar/daily/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'schedule.views.calendar_day', name = "d_calendar_date"),
    url(r'^calendar/(?P<calendar_slug>[-\w]+)/$', 'schedule.views.calendar', name="s_calendar"),

    url(r'^calendar/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar', name = "s_calendar_date"),
    url(r'^event/create/(?P<calendar_slug>[-\w]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/$', 'schedule.views.create_event', name='s_create_event_date'),

    #By calendar id
    url(r'^calendar/by_id/year/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_year', name="year_calendar_by_id"),
    url(r'^calendar/by_id/year/(?P<calendar_id>\d+)/(?P<year>\d+)/$', 'schedule.views.calendar_year', name="year_calendar_by_id_date"),
    url(r'^calendar/by_id/tri_month/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_tri_month', name="tri_month_calendar_by_id"),
    url(r'^calendar/by_id/tri_month/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_tri_month', name="tri_month_calendar_by_id_date"),
    url(r'^calendar/by_id/compact_month/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_compact_month', name="c_calendar_by_id"),
    url(r'^calendar/by_id/compact_month/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_compact_month', name = "c_calendar_by_id_date"),
    url(r'^calendar/by_id/month/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_month', name="m_calendar_by_id"),
    url(r'^calendar/by_month/month/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar_month', name = "m_calendar_by_id_date"),
    url(r'^calendar/week/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_week', name="w_calendar_by_id"),
    url(r'^calendar/week/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'schedule.views.calendar_week', name = "w_calendar_date_by_id"),
    url(r'^calendar/by_id/daily/(?P<calendar_id>\d+)/$', 'schedule.views.calendar_day', name="d_calendar_by_id"),
    url(r'^calendar/by_id/daily/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'schedule.views.calendar_day', name = "d_calendar_by_id_date"),
    url(r'^calendar/by_id/(?P<calendar_id>\d+)/$', 'schedule.views.calendar', name="s_calendar_by_id"),
    url(r'^calendar/by_id/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'schedule.views.calendar', name = "s_calendar_by_id_date"),
    url(r'^calendar/(?P<calendar_id>\d+)/create_event/$', 'schedule.views.create_or_edit_event', name="s_create_event_in_calendar"),
    url(r'^event/create/by_id/(?P<calendar_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)/$', 'schedule.views.create_event', name='s_create_event_by_id_date'),

    url(r'^event/create/$', 'schedule.views.create_or_edit_event', name='s_create_event'),
    url(r'^event/edit/(?P<event_id>\d+)/$', 'schedule.views.create_or_edit_event', name='s_edit_event'),
    url(r'^event/(?P<event_id>\d+)/$', 'schedule.views.event', name="s_event"),
    url(r'^event/delete/(?P<event_id>\d+)/$', 'schedule.views.delete_event', name="s_delete_event"),
    url(r'$', object_list, info_dict, name='schedule'),
)
