from django.core.management.base import NoArgsCommand

from django.core.management.color import no_style

class Command(NoArgsCommand):
    help = "Load some sample data into the db"

    def handle_noargs(self, **options):
        import datetime
        from schedule.models import Calendar
        from schedule.models import Event
        from schedule.models import Rule

        print "checking for existing data ..."
        try:
            cal = Calendar.objects.get(name="yml_cal")
            import ipdb; ipdb.set_trace()
            print "It looks like you already have loaded the sample data, quitting."
            import sys
            sys.exit(1)
        except Calendar.DoesNotExist:
            import ipdb; ipdb.set_trace()
            pass

        print "Create 2 calendars : tony_cal, yml_cal"
        yml_cal = Calendar(name="yml_cal")
        yml_cal.save()
        print "First calendar is created"
        tony_cal = Calendar(name="tony_cal")
        tony_cal.save()
        print "Second calendar is created"
        print "Create some events"
        
        data = {
                'title': 'Ping pong',
                'start': datetime.datetime(2008, 11, 1, 0, 0),
                'end': datetime.datetime(2010, 1, 10, 0, 0),
                'rule': Rule(frequency = "WEEKLY")
               }
        event = Event(**data)
        event.save()
        tony_cal.events.add(event)
