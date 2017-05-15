from django.db.models.signals import pre_save

from schedule.models import Calendar, Event


def optional_calendar(sender, **kwargs):
    event = kwargs.pop('instance')

    if not isinstance(event, Event):
        return True
    if not event.calendar:
        calendar, _created = Calendar.objects.get_or_create(
            name='default',
            defaults={'slug': 'default'})
        event.calendar = calendar
    return True


pre_save.connect(optional_calendar)
