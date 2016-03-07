from django.contrib import admin

from schedule.models import Calendar, Event, CalendarRelation, Rule
from schedule.forms import EventAdminForm

class CalendarAdminOptions(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm


admin.site.register(Calendar, CalendarAdminOptions)
admin.site.register(Event, EventAdmin)
admin.site.register([Rule, CalendarRelation])
