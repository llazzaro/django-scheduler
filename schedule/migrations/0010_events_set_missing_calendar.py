from django.db import migrations


def forwards(apps, schema_editor):
    Calendar = apps.get_model('schedule', 'Calendar')
    Event = apps.get_model('schedule', 'Event')
    calendar, _created = Calendar.objects.get_or_create(
        name='default',
        defaults={'slug': 'default'})
    Event.objects.filter(calendar=None).update(calendar=calendar)


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
