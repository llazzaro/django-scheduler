from django.db import migrations


def forwards(apps, schema_editor):
    Calendar = apps.get_model('schedule', 'Calendar')
    Event = apps.get_model('schedule', 'Event')
    events_qs = Event.objects.filter(calendar=None)
    # Only create the default Calendar object if events need it.
    if events_qs.exists():
        calendar, _created = Calendar.objects.get_or_create(
            name='default',
            defaults={'slug': 'default'})
        events_qs.update(calendar=calendar)


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0009_merge_20180108_2303'),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            migrations.RunPython.noop,
            elidable=True,
        )
    ]
