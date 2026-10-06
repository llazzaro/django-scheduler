"""Retrieve, cache, and classify occurrences for a calendar period.

Caches remain on the period, allowing sub-periods to share persisted occurrences
and preserving callbacks supplied by Period subclasses.
"""

from django.db.models.query import prefetch_related_objects


class PeriodOccurrences:
    def __init__(self, period, occurrence_model):
        self.period = period
        self.occurrence_model = occurrence_model

    def get_sorted(self):
        occurrences = []
        if (
            hasattr(self.period, "occurrence_pool")
            and self.period.occurrence_pool is not None
        ):
            for occurrence in self.period.occurrence_pool:
                if (
                    occurrence.start <= self.period.utc_end
                    and occurrence.end >= self.period.utc_start
                ):
                    occurrences.append(occurrence)
        else:
            prefetch_related_objects(self.period.events, "occurrence_set")
            for event in self.period.events:
                event_occurrences = event.get_occurrences(
                    self.period.start, self.period.end, clear_prefetch=False
                )
                occurrences += event_occurrences
        return sorted(occurrences, **self.period.sorting_options)

    def get_cached(self):
        if hasattr(self.period, "_occurrences"):
            return self.period._occurrences
        occs = self.period._get_sorted_occurrences()
        self.period._occurrences = occs
        return occs

    def get_persisted(self):
        if hasattr(self.period, "_persisted_occurrences"):
            return self.period._persisted_occurrences
        else:
            self.period._persisted_occurrences = self.occurrence_model.objects.filter(
                event__in=self.period.events
            )
            return self.period._persisted_occurrences

    def classify(self, occurrence, show_cancelled):
        if occurrence.cancelled and not show_cancelled:
            return
        if occurrence.start > self.period.end or occurrence.end < self.period.start:
            return None
        started = self.period.utc_start <= occurrence.start < self.period.utc_end
        ended = self.period.utc_start <= occurrence.end < self.period.utc_end
        if started and ended:
            return {"occurrence": occurrence, "class": 1}
        elif started:
            return {"occurrence": occurrence, "class": 0}
        elif ended:
            return {"occurrence": occurrence, "class": 3}
        # it existed during this period but it didn't begin or end within it
        # so it must have just continued
        return {"occurrence": occurrence, "class": 2}

    def get_partials(self):
        occurrence_dicts = []
        for occurrence in self.period.occurrences:
            occurrence = self.period.classify_occurrence(occurrence)
            if occurrence:
                occurrence_dicts.append(occurrence)
        return occurrence_dicts

    def has_occurrences(self):
        return any(self.period.classify_occurrence(o) for o in self.period.occurrences)
