class Occurrence(object):
    """
    An Occurrence is an incarnation of a recurring event for a given date.

    >>> data = {
    ...         'title': 'Recent Event',
    ...         'start': datetime.datetime(2008, 1, 5, 0, 0),
    ...         'end': datetime.datetime(2008, 1, 10, 0, 0),
    ...         'end_recurring_period' : datetime.datetime(2008, 5, 5, 0, 0),
    ...         'rules': 'opw',
    ...        }
    >>> recurring_event = RecurringEvent(**data)
    >>> recurring_event.save()
    >>> Occurrence = Occurrence(event=recurring_event,
    ...                        occurrence_start_date=datetime.datetime(2008, 1, 12, 0, 0),
    ...                        occurrence_end_date=datetime.datetime(2008, 1, 12, 0, 0))

    """
    def __init__(self,event,start,end):
        self.event = event
        self.start = start
        self.end = end

    def __unicode__(self):
        return "%s to %s" %(self.start, self.end)
    
    def __cmp__(self, other):
        rank = cmp(self.start, other.start)
        if rank == 0:
            return cmp(self.end, other.end)
        return rank
