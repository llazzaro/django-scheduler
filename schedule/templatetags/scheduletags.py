import datetime
from django.conf import settings
from django import template
from django.core.urlresolvers import reverse
from schedule.models import Calendar
from schedule.periods import weekday_names, weekday_abbrs

register = template.Library()

@register.inclusion_tag("schedule/_month_table.html")
def month_table( calendar, date, size="regular", uname=None ):
    month = calendar.get_month( date=date )
    if size == "small":
        context = {'day_names':weekday_abbrs}
    else:
        context = {'day_names':weekday_names}
    if uname:
        prev_url_context = { 'calendar_slug': calendar.slug,
                             'year': month.prev_month().year,
                             'month': month.prev_month().month
                           }
        context['prev_url'] = reverse( uname, kwargs=prev_url_context )
        next_url_context = { 'calendar_slug': calendar.slug,
                             'year': month.next_month().year,
                             'month': month.next_month().month
                           }
        context['next_url'] = reverse( uname, kwargs=next_url_context )
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
    prev_day = day.prev_day()
    prev_url_context = { 'calendar_slug': calendar.slug,
                         'year': prev_day.year,
                         'month': prev_day.month,
                         'day': prev_day.day
                       }
    context['prev_url'] = reverse( "d_calendar_date", kwargs=prev_url_context )
    next_day = day.next_day()
    next_url_context = { 'calendar_slug': calendar.slug,
                         'year': next_day.year,
                         'month': next_day.month,
                         'day': next_day.day
                        }
    context['next_url'] = reverse( "d_calendar_date", kwargs=next_url_context )
    return context

@register.inclusion_tag("schedule/_event_options.html")
def title_and_options( event ):
    context = {
        'event' : event,
        'MEDIA_URL' : getattr(settings, "MEDIA_URL"),
    }
    lookup_context = {
        'event_id': event.id
    }
    context['view_event'] = reverse( "s_event", kwargs=lookup_context )
    context['edit_event'] = reverse( "s_edit_event", kwargs=lookup_context )
    context['delete_event'] = reverse( "s_delete_event", kwargs=lookup_context )
    return context

@register.inclusion_tag("schedule/_create_event_options.html")
def create_event_url( calendar, slot ):
    context = {
        'calendar' : calendar,
        'MEDIA_URL' : getattr(settings, "MEDIA_URL"),
    }
    lookup_context = {
        'calendar_slug': calendar.slug,
        'year' : slot.year,
        'month' : slot.month,
        'day' : slot.day,
        'hour' : slot.hour,
        'minute' : slot.minute
    }
    context['create_event_url'] = reverse( "s_create_event_date", kwargs=lookup_context )
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

def querystring_for_date(date):
    return '?year=%d&month=%d&day=%d&hour=%d&minute=%d&second=%d' % (date.year, date.month, date.day, date.hour, date.minute, date.second)
register.simple_tag