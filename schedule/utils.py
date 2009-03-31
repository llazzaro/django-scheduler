import datetime
import heapq
from schedule.models import Occurrence


class EventListManager(object):
    """
    This class is responsible for doing functions on a list of events. It is
    used to when one has a list of events and wants to access the occurrences
    from these events in as a group
    """
    def __init__(self, events):
        self.events = events
    
    def occurrences_after(self, after=None):
        """
        It is often useful to know what the next occurrence is given a list of
        events.  This function produces a generator that yields the 
        the most recent occurrence after the date ``after`` from any of the
        events in ``self.events``
        """
        if after is None:
            after = datetime.datetime.now()
        persisted_occurrences = [(occurrence, occurrence) for occurrence in Occurrence.objects.filter(event__in = self.events)]
        persisted_occurrences = dict(persisted_occurrences)
        generators = [event._occurrences_after_generator(after) for event in self.events]
        occurrences = []
        
        for generator in generators:
            try:
                heapq.heappush(occurrences, (generator.next(), generator))
            except StopIteration:
                pass
        
        while True:
            generator=occurrences[0][1]
            try:
                next = heapq.heapreplace(occurrences, (generator.next(), generator))[0]
            except StopIteration:
                next = heapq.heappop(occurrences)
            yield persisted_occurrences.get(next, next)
    


        