from django import template
from schedule.models import Calendar

register = template.Library()

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