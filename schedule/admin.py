from django.contrib import admin

from .forms import CalendarForm, EventAdminForm
from .models import Calendar, CalendarRelation, Event, EventRelation, Occurrence, Rule


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    fieldsets = ((None, {"fields": [("name", "slug"), "color_event"]}),)
    form = CalendarForm


@admin.register(CalendarRelation)
class CalendarRelationAdmin(admin.ModelAdmin):
    list_display = ("calendar", "content_object")
    list_filter = ("inheritable",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "calendar",
                    ("content_type", "object_id", "distinction"),
                    "inheritable",
                ]
            },
        ),
    )


@admin.register(EventRelation)
class EventRelationAdmin(admin.ModelAdmin):
    list_display = ("event", "content_object", "distinction")
    fieldsets = (
        (None, {"fields": ["event", ("content_type", "object_id", "distinction")]}),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start", "end")
    list_filter = ("start",)
    ordering = ("-start",)
    date_hierarchy = "start"
    search_fields = ("title", "description")
    raw_id_fields = ("creator",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    ("title", "color_event"),
                    ("description",),
                    ("start", "end"),
                    ("creator", "calendar"),
                    ("rule", "end_recurring_period"),
                ]
            },
        ),
    )
    form = EventAdminForm


admin.site.register(Occurrence, admin.ModelAdmin)

# https://stackoverflow.com/questions/8007095/dynamic-fields-in-django-admin
# https://pypi.org/project/django-dynamic-admin-forms/ !! doesn't work in django 4
# XX https://django-constance.readthedocs.io/en/latest/


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("frequency",)
    search_fields = ("name", "description")
    fields = ("name", "description", "frequency", "repeats", "params")
    # form = RuleForm
    filter_horizontal = ["repeats"]
