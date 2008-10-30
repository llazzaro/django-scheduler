from django.contrib import admin

from schedule.models import Calendar, Event, CalendarRelation

admin.site.register([Event, Calendar, CalendarRelation])