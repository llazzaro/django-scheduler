from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Event(models.Model):
'''
Event:
Event's must be associate with a calendar, which will be the calendar it exists in,
and a user, which will be the author.
'''
    HIGH_PRIORITY = u'h'
    MEDIUM_PRIORITY = u'm'
    LOW_PRIORITY = u'l'

    PRIORITY_CHOICES = (
        (HIGH_PRIORITY, u'High Priority'),
        (MEDIUM_PRIORITY, u'Medium Priority'),
        (LOW_PRIORITY, u'Low Priority'),
    )
    title = models.CharField(max_length = 255)
    description = models.TextField()
    time = models.DateTimeField()
    author = models.ForeignKey(User)
    calendar = models.ForeignKey(Calendar)
    priority = models.IntField(choices=PRIORITY_CHOICES)

    date_created = models.DateTimeField()
    date_modified = mdoels.DateTimeField()

    def save(self):
    '''The save is overridden to set the data_created
       field and the data_modified field'''
        if not self.pk:
            self.date_created = datetime.now()
        date_modified = datetime.now()
        super(Event, self).save()

    class Admin:
        pass

class Calendar(models.Model):
'''Calendars:
Calendars will have three many to many relations with users.
These will be viewers, changers, and administrators.  It is important
to understand that modifiers are viewers, and administrators are modifiers and 
administrators'''

    viewers = models.ManyToManyField(User)
    modifiers = models.ManyToManyField(User)
    administrators = models.ManyToManyField(User)

    class Admin:
        pass
    
