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
            print "Sample data not found in db."
            print "Install it..."


        print "Create 2 calendars : tony_cal, yml_cal"
        yml_cal = Calendar(name="yml_cal")
        yml_cal.save()
        print "First calendar is created"
        tony_cal = Calendar(name="tony_cal")
        tony_cal.save()
        print "Second calendar is created"
        print "Create some events"
        rule = Rule(frequency = "WEEKLY")
        rule.save()
        data = {
                'title': 'Ping pong',
                'start': datetime.datetime(2008, 11, 1, 8, 0),
                'end': datetime.datetime(2008, 11, 1, 9, 0),
                'end_recurring_period' : datetime.datetime(2010, 5, 5, 0, 0),
                'rule': rule
               }
        event = Event(**data)
        event.save()
        tony_cal.events.add(event)
