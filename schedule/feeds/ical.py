import icalendar
from django.http import HttpResponse, HttpResponseNotFound

EVENT_ITEMS = (
    ("uid", "uid"),
    ("dtstart", "start"),
    ("dtend", "end"),
    ("summary", "summary"),
    ("location", "location"),
    ("last_modified", "last_modified"),
    ("created", "created"),
)


class ICalendarFeed:
    def __call__(self, *args, **kwargs):
        from schedule.models import Calendar

        self.args = args
        self.kwargs = kwargs

        try:
            cal = icalendar.Calendar()
            cal.add("prodid", "-// django-scheduler //")
            cal.add("version", "2.0")

            for item in list(self.items()):
                event = icalendar.Event()

                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, "item_" + key)(item)
                    if value:
                        event.add(vkey, value)

                cal.add_component(event)

            response = HttpResponse(cal.to_ical())
            response["Content-Type"] = "text/calendar"

            return response
        except Calendar.DoesNotExist:
            return HttpResponseNotFound("<h1>Calendar not found</h1>")

    def items(self):
        return []

    def item_uid(self, item):
        pass

    def item_start(self, item):
        pass

    def item_end(self, item):
        pass

    def item_summary(self, item):
        return str(item)

    def item_location(self, item):
        pass

    def item_last_modified(self, item):
        pass

    def item_created(self, item):
        pass
