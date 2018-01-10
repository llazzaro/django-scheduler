from django.db import models

from schedule.models import AbstractCalendar, AbstractEvent, AbstractOccurrence


class CustomCalendar(AbstractCalendar):
    color = models.CharField(max_length=50)


class CustomEvent(AbstractEvent):
    last_read_at = models.DateTimeField(null=True)


class CustomOccurrence(AbstractOccurrence):
    is_ready = models.BooleanField(default=False)
