from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("schedule", "0007_merge_text_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="calendarrelation",
            name="object_id",
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name="eventrelation",
            name="object_id",
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterIndexTogether(
            name="calendarrelation", index_together={("content_type", "object_id")}
        ),
        migrations.AlterIndexTogether(
            name="eventrelation", index_together={("content_type", "object_id")}
        ),
        # Drop db_index before creating unique index, to prevent re-creating indices
        migrations.RunSQL(
            "DROP INDEX IF EXISTS schedule_calendar_slug_ba17e861; "
            "DROP INDEX IF EXISTS schedule_calendar_slug_ba17e861_like;"
        ),
        migrations.AlterField(
            model_name="calendar",
            name="slug",
            field=models.SlugField(verbose_name="slug", max_length=200, unique=True),
        ),
    ]
