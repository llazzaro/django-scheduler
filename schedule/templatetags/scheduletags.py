import datetime
from django.conf import settings
from django import template
from django.core.urlresolvers import reverse
from django.utils.dateformat import format
from schedule.models import Calendar
from schedule.periods import weekday_names, weekday_abbrs,  Month

register = template.Library()

@register.inclusion_tag("schedule/_month_table.html")
def month_table( calendar, month, size="regular", shift=None):
    if shift:
        if shift == -1:
            month = Month(calendar.events.all(), month.prev())
        if shift == 1:
            month = Month(calendar.events.all(), month.next())
    if size == "small":
        context = {'day_names':weekday_abbrs}
    else:
        context = {'day_names':weekday_names}
    context['calendar'] = calendar
    context['month'] = month
    context['size'] = size
    return context

@register.inclusion_tag("schedule/_day_cell.html")
def day_cell( calendar, day, month, size="regular" ):
    return {
        'calendar' : calendar,
        'day' : day,
        'month' : month,
        'size' : size
    }

@register.inclusion_tag("schedule/_daily_table.html")
def daily_table( calendar, day ):
    td30 = datetime.timedelta(minutes=30)
    morning = day.start
    afternoon = day.start  + datetime.timedelta(hours=12)
    morning_period = day.get_time_slot( morning, morning + td30 )
    afternoon_period = day.get_time_slot( afternoon, afternoon + td30 )
    day_slots = [ (morning_period, afternoon_period) ]
    for i in range(23):
        morning += td30
        afternoon += td30
        morning_period = day.get_time_slot( morning, morning + td30 )
        afternoon_period = day.get_time_slot( afternoon, afternoon + td30 )
        day_slots.append( (morning_period, afternoon_period) )
    context = {
        'calendar' : calendar,
        'day' : day,
        'day_slots' : day_slots,
        'MEDIA_URL' : getattr(settings, "MEDIA_URL"),
    }
    return context

@register.inclusion_tag("schedule/_event_options.html")
def title_and_options( occurrence ):
    context = {
        'occurrence' : occurrence,
        'MEDIA_URL' : getattr(settings, "MEDIA_URL"),
    }
    context['view_occurrence'] = occurrence.get_absolute_url()
    context['edit_occurrence'] = occurrence.get_edit_url()
    context['cancel_occurrence'] = occurrence.get_cancel_url()
    return context

@register.inclusion_tag("schedule/_create_event_options.html")
def create_event_url( calendar, slot ):
    context = {
        'calendar' : calendar,
        'MEDIA_URL' : getattr(settings, "MEDIA_URL"),
    }
    lookup_context = {
        'calendar_slug': calendar.slug,
    }
    context['create_event_url'] ="%s%s" % (
        reverse( "calendar_create_event", kwargs=lookup_context),
        querystring_for_date(slot))
    return context

class CalendarNode(template.Node):
    def __init__(self, content_object, distinction, context_var, create=False):
        self.content_object = template.Variable(content_object)
        self.distinction = distinction
        self.context_var = context_var

    def render(self, context):
        calendar = Calendar.objects.get_calendar_for_object(self.content_object.resolve(context), self.distinction)
        context[self.context_var] = Calendar.objects.get_calendar_for_object(self.content_object.resolve(context), self.distinction)
        return ''

def do_get_calendar_for_object(parser, token):
    contents = token.split_contents()
    if len(contents) == 4:
        tag_name, content_object, _, context_var = contents
        distinction = None
    elif len(contents) == 5:
        tag_name, content_object, distinction, _, context_var = token.split_contents()
    else:
        raise template.TemplateSyntaxError, "%r tag follows form %r <content_object> as <context_var>" % (token.contents.split()[0], token.contents.split()[0])
    return CalendarNode(content_object, distinction, context_var)

class CreateCalendarNode(template.Node):
    def __init__(self, content_object, distinction, context_var, name):
        self.content_object = template.Variable(content_object)
        self.distinction = distinction
        self.context_var = context_var
        self.name = name

    def render(self, context):
        context[self.context_var] = Calendar.objects.get_or_create_calendar_for_object(self.content_object.resolve(context), self.distinction, name = self.name)
        return ''

def do_get_or_create_calendar_for_object(parser, token):
    contents = token.split_contents()
    if len(contents) > 2:
        tag_name = contents[0]
        obj = contents[1]
        if 'by' in contents:
            by_index = contents.index('by')
            distinction = contents[by_index+1]
        else:
            distinction = None
        if 'named' in contents:
            named_index = contents.index('named')
            name = contents[named_index+1]
            if name[0] == name[-1]:
                name = name[1:-1]
        else:
            name = None
        if 'as' in contents:
            as_index = contents.index('as')
            context_var = contents[as_index+1]
        else:
            raise template.TemplateSyntaxError, "%r tag requires an a context variable: %r <content_object> [named <calendar name>] [by <distinction>] as <context_var>" % (token.split_contents()[0], token.split_contents()[0])
    else:
        raise template.TemplateSyntaxError, "%r tag follows form %r <content_object> [named <calendar name>] [by <distinction>] as <context_var>" % (token.split_contents()[0], token.split_contents()[0])
    return CreateCalendarNode(obj, distinction, context_var, name)

register.tag('get_calendar', do_get_calendar_for_object)
register.tag('get_or_create_calendar', do_get_or_create_calendar_for_object)

@register.simple_tag
def querystring_for_date(date, num=6):
    query_string = '?'
    qs_parts = ['year=%d', 'month=%d', 'day=%d', 'hour=%d', 'minute=%d', 'second=%d']
    qs_vars = (date.year, date.month, date.day, date.hour, date.minute, date.second)
    query_string += '&'.join(qs_parts[:num]) % qs_vars[:num]
    return query_string

@register.simple_tag
def prev_url(target, slug, period):
    return '%s%s' % (
        reverse(target, kwargs=dict(calendar_slug=slug)),
            querystring_for_date(period.prev()))

@register.simple_tag
def next_url(target, slug, period):
    return '%s%s' % (
        reverse(target, kwargs=dict(calendar_slug=slug)),
            querystring_for_date(period.next()))

@register.inclusion_tag("schedule/_prevnext.html")
def prevnext( target, slug, period, fmt=None):
    if fmt is None:
        fmt = settings.DATE_FORMAT
    context = {
        'slug' : slug,
        'period' : period,
        'period_name': format(period.start, fmt),
        'target':target,
    }
    return context

