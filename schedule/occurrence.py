from django.utils.translation import ugettext

class Occurrence(object):
    """
    An Occurrence is an incarnation of a recurring event for a given date.

    """
    def __init__(self,event,start,end):
        self.event = event
        self.start = start
        self.end = end

    def __unicode__(self):
        return ugettext("%(start)s to %(end)s") % {
            'start': self.start,
            'end': self.end,
        }

    def __cmp__(self, other):
        rank = cmp(self.start, other.start)
        if rank == 0:
            return cmp(self.end, other.end)
        return rank
