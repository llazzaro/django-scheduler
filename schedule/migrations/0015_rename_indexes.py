from django.db import migrations, models


class Migration(migrations.Migration):
    """Replace index_together with Meta.indexes.

    Django 5.0 removed the Meta.index_together option. This migration
    updates the migration state from index_together to Meta.indexes
    without altering the database — the existing composite indexes
    created by earlier migrations are functionally identical.
    """

    dependencies = [
        ("schedule", "0014_use_autofields_for_pk"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterIndexTogether(
                    name="calendarrelation",
                    index_together=set(),
                ),
                migrations.AlterIndexTogether(
                    name="event",
                    index_together=set(),
                ),
                migrations.AlterIndexTogether(
                    name="eventrelation",
                    index_together=set(),
                ),
                migrations.AlterIndexTogether(
                    name="occurrence",
                    index_together=set(),
                ),
                migrations.AddIndex(
                    model_name="calendarrelation",
                    index=models.Index(
                        fields=["content_type", "object_id"],
                        name="schedule_ca_content_cddadb_idx",
                    ),
                ),
                migrations.AddIndex(
                    model_name="event",
                    index=models.Index(
                        fields=["start", "end"],
                        name="schedule_ev_start_a258cb_idx",
                    ),
                ),
                migrations.AddIndex(
                    model_name="eventrelation",
                    index=models.Index(
                        fields=["content_type", "object_id"],
                        name="schedule_ev_content_6ceecb_idx",
                    ),
                ),
                migrations.AddIndex(
                    model_name="occurrence",
                    index=models.Index(
                        fields=["start", "end"],
                        name="schedule_oc_start_76a2f8_idx",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
