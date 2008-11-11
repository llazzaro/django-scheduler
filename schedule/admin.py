from django.contrib import admin

from schedule.models import Calendar, Event, CalendarRelation, Rule

admin.site.register([Rule, Event, Calendar, CalendarRelation])
