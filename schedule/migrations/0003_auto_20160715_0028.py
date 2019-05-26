from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("schedule", "0002_event_color_event")]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="end",
            field=models.DateTimeField(
                help_text="The end time must be later than the start time.",
                verbose_name="end",
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="end_recurring_period",
            field=models.DateTimeField(
                help_text="This date is ignored for one time only events.",
                null=True,
                verbose_name="end recurring period",
                db_index=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="start",
            field=models.DateTimeField(verbose_name="start", db_index=True),
        ),
        migrations.AlterField(
            model_name="occurrence",
            name="end",
            field=models.DateTimeField(verbose_name="end", db_index=True),
        ),
        migrations.AlterField(
            model_name="occurrence",
            name="start",
            field=models.DateTimeField(verbose_name="start", db_index=True),
        ),
        migrations.AlterIndexTogether(name="event", index_together={("start", "end")}),
        migrations.AlterIndexTogether(
            name="occurrence", index_together={("start", "end")}
        ),
    ]
