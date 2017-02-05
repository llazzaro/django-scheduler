from django.db.models.signals import pre_save

from schedule.models import Event, Calendar


def optional_calendar(sender, **kwargs):
    event = kwargs.pop('instance')

    if not isinstance(event, Event):
        return True
    if not event.calendar:
        try:
            calendar = Calendar.objects.get(name='default')
        except Calendar.DoesNotExist:
            calendar = Calendar(name='default', slug='default')
            calendar.save()

        event.calendar = calendar
    return True


pre_save.connect(optional_calendar)
