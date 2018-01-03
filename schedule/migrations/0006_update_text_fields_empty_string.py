from django.db import migrations


def forwards(apps, schema_editor):
    model_fields = [
        ('CalendarRelation', ['distinction']),
        ('Event', ['color_event', 'description']),
        ('EventRelation', ['distinction']),
        ('Occurrence', ['description', 'title']),
        ('Rule', ['params']),
    ]
    for model_name, fields in model_fields:
        model_class = apps.get_model('schedule', model_name)
        for field_name in fields:
            model_class.objects.filter(**{field_name: None}).update(**{field_name: ''})


def reverse(apps, schema_editor):
    model_fields = [
        ('CalendarRelation', ['distinction']),
        ('Event', ['color_event', 'description']),
        ('EventRelation', ['distinction']),
        ('Occurrence', ['description', 'title']),
        ('Rule', ['params']),
    ]
    for model_name, fields in model_fields:
        model_class = apps.get_model('schedule', model_name)
        for field_name in fields:
            model_class.objects.filter(**{field_name: ''}).update(**{field_name: None})


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_auto_20160715_0028'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse, elidable=True),
    ]
