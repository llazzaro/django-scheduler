from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from schedule import utils
from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence


def check_event_perms(ob, user):
    return user.username == "ann"


def check_calendar_perms(ob, user):
    return user.username == "bob"


class TestPermissions(TestCase):
    def setUp(self):
        User.objects.create_user(username="ann", password="ann")
        User.objects.create_user(username="bob", password="bob")

        self.cal1 = Calendar.objects.create(name="cal1", slug="cal1")
        self.cal2 = Calendar.objects.create(name="cal2", slug="cal2")

        self.event1 = Event.objects.create(
            start=timezone.now(), end=timezone.now(), title="event1", calendar=self.cal1
        )
        self.event2 = Event.objects.create(
            start=timezone.now(), end=timezone.now(), title="event2", calendar=self.cal2
        )

        self.occ1 = Occurrence.objects.create(
            event=self.event1,
            start=self.event1.start,
            end=self.event1.end,
            original_start=self.event1.start,
            original_end=self.event1.end,
        )
        self.occ2 = Occurrence.objects.create(
            event=self.event2,
            start=self.event2.start,
            end=self.event2.end,
            original_start=self.event2.start,
            original_end=self.event2.end,
        )

        self.urls_to_check = [
            reverse("calendar_create_event", kwargs={"calendar_slug": self.cal1.slug}),
            reverse(
                "edit_event",
                kwargs={"calendar_slug": self.cal1.slug, "event_id": self.event1.id},
            ),
            reverse("delete_event", kwargs={"event_id": self.event1.id}),
            self.occ1.get_edit_url(),
            self.occ1.get_cancel_url(),
        ]

    def _check_protected_urls(self, should_allow):
        for url in self.urls_to_check:
            response = self.client.get(url)
            if should_allow:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 302)

    def test_event_perms(self):
        # ann has event rights, bob don't
        default_event_check = utils.CHECK_EVENT_PERM_FUNC
        utils.CHECK_EVENT_PERM_FUNC = check_event_perms

        self.client.login(username="ann", password="ann")
        self._check_protected_urls(should_allow=True)

        self.client.login(username="bob", password="bob")
        self._check_protected_urls(should_allow=False)

        utils.CHECK_EVENT_PERM_FUNC = default_event_check

    def test_calendar_perms(self):
        # bob has calendar rights, ann don't
        default_cal_check = utils.CHECK_CALENDAR_PERM_FUNC
        utils.CHECK_CALENDAR_PERM_FUNC = check_calendar_perms

        self.client.login(username="ann", password="ann")
        self._check_protected_urls(should_allow=False)

        self.client.login(username="bob", password="bob")
        self._check_protected_urls(should_allow=True)
        utils.CHECK_CALENDAR_PERM_FUNC = default_cal_check

    def test_calendar_and_event_perms(self):
        # two mutually exclusive functions, nor ann or bob has rights to access protected views
        default_event_check = utils.CHECK_EVENT_PERM_FUNC
        default_cal_check = utils.CHECK_CALENDAR_PERM_FUNC
        utils.CHECK_EVENT_PERM_FUNC = check_event_perms
        utils.CHECK_CALENDAR_PERM_FUNC = check_calendar_perms

        self.client.login(username="ann", password="ann")
        self._check_protected_urls(should_allow=False)

        self.client.login(username="bob", password="bob")
        self._check_protected_urls(should_allow=False)

        utils.CHECK_EVENT_PERM_FUNC = default_event_check
        utils.CHECK_CALENDAR_PERM_FUNC = default_cal_check
