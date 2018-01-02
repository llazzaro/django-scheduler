from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_merge_text_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendar',
            name='slug',
            field=models.SlugField(verbose_name='slug', max_length=200, unique=True),
        ),
    ]
