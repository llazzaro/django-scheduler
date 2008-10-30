from django.contrib.admin import site

from models import Calendar
from models import Event

site.register(Calendar)
site.register(Event)