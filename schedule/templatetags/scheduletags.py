from __future__ import division
from django.utils.six.moves.builtins import range
import datetime
from django.conf import settings
from django import template
from django.core.urlresolvers import reverse
from django.utils.dateformat import format
from django.utils.html import escape
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.six.moves.urllib.parse import urlencode

from schedule.settings import CHECK_EVENT_PERM_FUNC, CHECK_CALENDAR_PERM_FUNC, SCHEDULER_PREVNEXT_LIMIT_SECONDS
from schedule.models import Calendar
from schedule.periods import weekday_names, weekday_abbrs

register = template.Library()


@register.inclusion_tag('schedule/_month_table.html', takes_context=True)
def month_table(context, calendar, month, size='regular', shift=None):
    if shift:
        if shift == -1:
            month = month.prev()
        if shift == 1:
            month = next(month)
    if size == 'small':
        context['day_names'] = weekday_abbrs
    else:
        context['day_names'] = weekday_names
    context['calendar'] = calendar
    context['month'] = month
    context['size'] = size
    return context


@register.inclusion_tag('schedule/_day_cell.html', takes_context=True)
def day_cell(context, calendar, day, month, size='regular'):
    context.update({
        'calendar': calendar,
        'day': day,
        'month': month,
        'size': size
    })
    return context


@register.inclusion_tag('schedule/_daily_table.html', takes_context=True)
def daily_table(context, day, start=8, end=20, increment=30):
    """
      Display a nice table with occurrences and action buttons.
      Arguments:
      start - hour at which the day starts
      end - hour at which the day ends
      increment - size of a time slot (in minutes)
    """
    user = context['request'].user
    addable = CHECK_EVENT_PERM_FUNC(None, user)
    if 'calendar' in context:
        addable &= CHECK_CALENDAR_PERM_FUNC(context['calendar'], user)
    context['addable'] = addable
    day_part = day.get_time_slot(day.start + datetime.timedelta(hours=start), day.start + datetime.timedelta(hours=end))
    # get slots to display on the left
    slots = _cook_slots(day_part, increment)
    context['slots'] = slots
    return context


@register.inclusion_tag('schedule/_event_title.html', takes_context=True)
def title(context, occurrence):
    context.update({
        'occurrence': occurrence,
    })
    return context


@register.inclusion_tag('schedule/_event_options.html', takes_context=True)
def options(context, occurrence):
    context.update({
        'occurrence': occurrence,
        'MEDIA_URL': getattr(settings, 'MEDIA_URL'),
    })
    context['view_occurrence'] = occurrence.get_absolute_url()
    user = context['request'].user
    if CHECK_EVENT_PERM_FUNC(occurrence.event, user) and CHECK_CALENDAR_PERM_FUNC(occurrence.event.calendar, user):
        context['edit_occurrence'] = occurrence.get_edit_url()
        context['cancel_occurrence'] = occurrence.get_cancel_url()
        context['delete_event'] = reverse('delete_event', args=(occurrence.event.id,))
        context['edit_event'] = reverse('edit_event', args=(occurrence.event.calendar.slug, occurrence.event.id,))
    else:
        context['edit_event'] = context['delete_event'] = ''
    return context


@register.inclusion_tag('schedule/_create_event_options.html', takes_context=True)
def create_event_url(context, calendar, slot):
    context.update({
        'calendar': calendar,
        'MEDIA_URL': getattr(settings, 'MEDIA_URL'),
    })
    lookup_context = {
        'calendar_slug': calendar.slug,
    }
    context['create_event_url'] = '%s%s' % (
        reverse('calendar_create_event', kwargs=lookup_context),
        querystring_for_date(slot))
    return context


class CalendarNode(template.Node):
    def __init__(self, content_object, distinction, context_var, create=False):
        self.content_object = template.Variable(content_object)
        self.distinction = distinction
        self.context_var = context_var

    def render(self, context):
        Calendar.objects.get_calendar_for_object(self.content_object.resolve(context), self.distinction)
        context[self.context_var] = Calendar.objects.get_calendar_for_object(self.content_object.resolve(context), self.distinction)
        return ''


@register.tag
def get_calendar(parser, token):
    contents = token.split_contents()
    if len(contents) == 4:
        _, content_object, _, context_var = contents
        distinction = None
    elif len(contents) == 5:
        _, content_object, distinction, _, context_var = token.split_contents()
    else:
        raise template.TemplateSyntaxError("%r tag follows form %r <content_object> as <context_var>" % (token.contents.split()[0], token.contents.split()[0]))
    return CalendarNode(content_object, distinction, context_var)


class CreateCalendarNode(template.Node):
    def __init__(self, content_object, distinction, context_var, name):
        self.content_object = template.Variable(content_object)
        self.distinction = distinction
        self.context_var = context_var
        self.name = name

    def render(self, context):
        context[self.context_var] = Calendar.objects.get_or_create_calendar_for_object(self.content_object.resolve(context), self.distinction, name=self.name)
        return ''


@register.tag
def get_or_create_calendar(parser, token):
    contents = token.split_contents()
    if len(contents) > 2:
        obj = contents[1]
        if 'by' in contents:
            by_index = contents.index('by')
            distinction = contents[by_index + 1]
        else:
            distinction = None
        if 'named' in contents:
            named_index = contents.index('named')
            name = contents[named_index + 1]
            if name[0] == name[-1]:
                name = name[1:-1]
        else:
            name = None
        if 'as' in contents:
            as_index = contents.index('as')
            context_var = contents[as_index + 1]
        else:
            raise template.TemplateSyntaxError("%r tag requires an a context variable: %r <content_object> [named <calendar name>] [by <distinction>] as <context_var>" % (token.split_contents()[0], token.split_contents()[0]))
    else:
        raise template.TemplateSyntaxError("%r tag follows form %r <content_object> [named <calendar name>] [by <distinction>] as <context_var>" % (token.split_contents()[0], token.split_contents()[0]))
    return CreateCalendarNode(obj, distinction, context_var, name)


@register.simple_tag
def querystring_for_date(date, num=6):
    qs_parts = [
        ('year', date.year),
        ('month', date.month),
        ('day', date.day),
        ('hour', date.hour),
        ('minute', date.minute),
        ('second', date.second),
    ]
    query_string = '?' + urlencode(qs_parts[:num])
    # For compatibility with older Django versions, escape the
    # output. Starting with Django 1.9, simple_tags are automatically
    # passed through conditional_escape(). See:
    # https://docs.djangoproject.com/en/1.9/releases/1.9/#simple-tag-now-wraps-tag-output-in-conditional-escape
    return escape(query_string)


@register.simple_tag
def prev_url(target, calendar, period):
    now = timezone.now()
    delta = now - period.prev().start
    slug = calendar.slug
    if delta.total_seconds() > SCHEDULER_PREVNEXT_LIMIT_SECONDS:
        return ''

    return mark_safe('<a href="%s%s"><span class="glyphicon glyphicon-circle-arrow-left"></span></a>' % (
        reverse(target, kwargs=dict(calendar_slug=slug)),
        querystring_for_date(period.prev().start)))


@register.simple_tag
def next_url(target, calendar, period):
    now = timezone.now()
    slug = calendar.slug

    delta = period.next().start - now
    if delta.total_seconds() > SCHEDULER_PREVNEXT_LIMIT_SECONDS:
        return ''

    return mark_safe('<a href="%s%s"><span class="glyphicon glyphicon-circle-arrow-right"></span></a>' % (
        reverse(target, kwargs=dict(calendar_slug=slug)),
        querystring_for_date(period.next().start)))


@register.inclusion_tag('schedule/_prevnext.html')
def prevnext(target, calendar, period, fmt=None):
    if fmt is None:
        fmt = settings.DATE_FORMAT
    context = {
        'calendar': calendar,
        'period': period,
        'period_name': format(period.start, fmt),
        'target': target,
    }
    return context


@register.inclusion_tag('schedule/_detail.html')
def detail(occurrence):
    context = {
        'occurrence': occurrence,
    }
    return context


def _cook_slots(period, increment):
    """
        Prepare slots to be displayed on the left hand side
        calculate dimensions (in px) for each slot.
        Arguments:
        period - time period for the whole series
        increment - slot size in minutes
    """
    tdiff = datetime.timedelta(minutes=increment)
    num = int((period.end - period.start).total_seconds()) // int(tdiff.total_seconds())
    s = period.start
    slots = []
    for i in range(num):
        sl = period.get_time_slot(s, s + tdiff)
        slots.append(sl)
        s = s + tdiff
    return slots


@register.simple_tag
def hash_occurrence(occ):
    return '%s_%s' % (occ.start.strftime('%Y%m%d%H%M%S'), occ.event.id)
