from django import template
from schedule.models import Calendar

register = template.Library()

class CalendarNode(template.Node):
    def __init__(self, content_object, distinction):
        self.content_object = template.Variable(content_object)
        self.distinction = distinction
    
    def render(self, context):
        context['calendar'] = Calendar.objects.get_calendar_for_object(self.content_object.resolve(context), self.distinction)
        return ''

def do_get_calendar_for_object(parser, token):
    if len(token.split_contents()) == 2:
        tag_name, content_object = token.split_contents()
        distinction = None
    elif len(token.split_contents()) == 3:
        tag_name, content_object, distinction = token.split_contents()
    else:
        raise template.TemplateSyntaxError, "%r tag requires only one argument" % token.contents.split()[0]
    return CalendarNode(content_object, distinction)
    
register.tag('get_calendar_for_object', do_get_calendar_for_object)