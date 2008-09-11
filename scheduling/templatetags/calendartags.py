from django import template
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from models import Event

register = template.Library()

def calendar_as_table(events, title, table):
'''
This inclusion tag renders a calendar as an html table element. 
'''

def calender_nameless

def calendar_weekless    

register.inclusion_tag('extra/client_info.html')(show_client_info)

def _get_events_daywise(events):
    """
    This helper function creates a dictionary that maps of days of a month to
    lists of 2-tuples.  This tuple will consist of an event and the word, 
    'begin', 'continue', 'end'.  This data could be used to construct a html 
    calendar. 
    """