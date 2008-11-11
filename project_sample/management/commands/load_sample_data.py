from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
    )
    help = "Load some sample data into the db"

    def handle_noargs(self, **options):
        from schedule.models import Calendar
        from schedule.models import Event

        print "checking for existing data ..."
        try:
            cal = Calendar.objects.get(name="yml_cal")
            print "It looks like you already have loaded the sample data, quitting."
            import sys
            sys.exit(1)
        except Calendar.DoesNotExist:
            pass

        print "Create 2 calendars : tony_cal, yml_cal"
        yml_cal = Calendar(name="yml-cal")
        yml_cal.save()
        tony_cal = Calendar(name="tony-cal")
        tony_cal.save()
        data = {
                'title': 'Ping pong',
                'start': datetime.datetime(2008, 11, 1, 0, 0),
                'end': datetime.datetime(2010, 1, 10, 0, 0)
               }
        event = Event(**data)
        event.save()
        tony_cal.events.add(event)
