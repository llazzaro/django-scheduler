from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ScheduleConfig(AppConfig):
    name = "schedule"
    verbose_name = _("Schedules")
    default_auto_field = "django.db.models.AutoField"
