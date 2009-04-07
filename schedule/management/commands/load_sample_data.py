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
            print "It looks like you already have loaded the sample data, quitting."
            import sys
            sys.exit(1)
        except Calendar.DoesNotExist:
            print "Sample data not found in db."
            print "Install it..."


        print "Create 2 calendars : tony_cal, yml_cal"
        yml_cal = Calendar(name="yml_cal",slug="yml")
        yml_cal.save()
        print "First calendar is created"
        tony_cal = Calendar(name="tony_cal",slug="tony")
        tony_cal.save()
        print "Second calendar is created"
        print "Do we need to create the most common rules?"
        try:
            rule = Rule.objects.get(name="Daily")
        except Rule.DoesNotExist:
            rule = Rule(frequency = "YEARLY", name = "Yearly", description = "will recur once every Year")
            rule.save()
            print "YEARLY recurrence created"
            rule = Rule(frequency = "MONTHLY", name = "Monthly", description = "will recur once every Month")
            rule.save()
            print "Monthly recurrence created"
            rule = Rule(frequency = "WEEKLY", name = "Weekly", description = "will recur once every Week")
            rule.save()
            print "Weekly recurrence created"
            rule = Rule(frequency = "DAILY", name = "Daily", description = "will recur once every Day")
            rule.save()
            print "Daily recurrence created"
        print "The common rules are installed."

        print "Create some events"
        rule = Rule.objects.get(frequency="WEEKLY")
        data = {
                'title': 'Ping pong',
                'start': datetime.datetime(2008, 11, 1, 8, 0),
                'end': datetime.datetime(2008, 11, 1, 9, 0),
                'end_recurring_period' : datetime.datetime(2010, 5, 5, 0, 0),
                'rule': rule,
                'calendar': tony_cal
               }
        event = Event(**data)
        event.save()
        rule = Rule.objects.get(frequency="DAILY")
        data = {
                'title': 'Home work',
                'start': datetime.datetime(2008, 11, 1, 18, 0),
                'end': datetime.datetime(2008, 11, 1, 19, 0),
                'end_recurring_period' : datetime.datetime(2010, 5, 5, 0, 0),
                'rule': rule,
                'calendar': tony_cal
               }
        event = Event(**data)
        event.save()
