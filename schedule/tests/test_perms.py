# coding=utf-8
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence
from schedule.conf import settings
from schedule import utils


def check_event_perms(ob, user):
    return user.username == 'admin'


def check_calendar_perms(ob, user):
    return user.username == 'user'


class TestPermissions(TestCase):
    def setUp(self):
        user_admin = User.objects.create_user(username='admin', password='admin')
        user_user = User.objects.create_user(username='user', password='user')

        self.cal1 = Calendar.objects.create(name='cal1', slug='cal1')
        self.cal2 = Calendar.objects.create(name='cal2', slug='cal2')

        self.event1 = Event.objects.create(start=timezone.now(), end=timezone.now(), title='event1', calendar=self.cal1)
        self.event2 = Event.objects.create(start=timezone.now(), end=timezone.now(), title='event2', calendar=self.cal2)

        self.occ1 = Occurrence.objects.create(event=self.event1, start=self.event1.start, end=self.event1.end,
                                              original_start=self.event1.start, original_end=self.event1.end)
        self.occ2 = Occurrence.objects.create(event=self.event2, start=self.event2.start, end=self.event2.end,
                                              original_start=self.event2.start, original_end=self.event2.end)

    @override_settings(LOGIN_URL='/admin/login/')
    def test_event_perms(self):
        # admin has event rights, user don't
        self.DEFAULT_CHECK_FUNC = settings.CHECK_EVENT_PERM_FUNC
        utils.CHECK_EVENT_PERM_FUNC = check_event_perms

        self.client.login(username='admin', password='admin')

        response = self.client.get(reverse('calendar_create_event', kwargs={'calendar_slug': self.cal1.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('edit_event', kwargs={'calendar_slug': self.cal1.slug, 'event_id': self.event1.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('delete_event', kwargs={'event_id': self.event1.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.occ1.get_edit_url())
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.occ1.get_cancel_url())
        self.assertEqual(response.status_code, 200)

        self.client.login(username='user', password='user')

        response = self.client.get(reverse('calendar_create_event', kwargs={'calendar_slug': self.cal1.slug}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('edit_event', kwargs={'calendar_slug': self.cal1.slug, 'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('delete_event', kwargs={'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_edit_url())
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_cancel_url())
        self.assertRedirects(response, '/admin/login/')

        utils.CHECK_EVENT_PERM_FUNC = self.DEFAULT_CHECK_FUNC

    @override_settings(LOGIN_URL='/admin/login/')
    def test_event_perms(self):
        # two mutually exclusive functions, nor admin or user has rights to access protected views
        self.DEFAULT_EVENT_CHECK_FUNC = settings.CHECK_EVENT_PERM_FUNC
        self.DEFAULT_CALENDAR_CHECK_FUNC = settings.CHECK_EVENT_PERM_FUNC
        utils.CHECK_EVENT_PERM_FUNC = check_event_perms
        utils.CHECK_CALENDAR_PERM_FUNC = check_calendar_perms

        self.client.login(username='admin', password='admin')

        response = self.client.get(reverse('calendar_create_event', kwargs={'calendar_slug': self.cal1.slug}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('edit_event', kwargs={'calendar_slug': self.cal1.slug, 'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('delete_event', kwargs={'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_edit_url())
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_cancel_url())
        self.assertRedirects(response, '/admin/login/')

        self.client.login(username='user', password='user')

        response = self.client.get(reverse('calendar_create_event', kwargs={'calendar_slug': self.cal1.slug}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('edit_event', kwargs={'calendar_slug': self.cal1.slug, 'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(reverse('delete_event', kwargs={'event_id': self.event1.id}))
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_edit_url())
        self.assertRedirects(response, '/admin/login/')
        response = self.client.get(self.occ1.get_cancel_url())
        self.assertRedirects(response, '/admin/login/')

        utils.CHECK_EVENT_PERM_FUNC = self.DEFAULT_EVENT_CHECK_FUNC
        utils.CHECK_CALENDAR_PERM_FUNC = self.DEFAULT_CALENDAR_CHECK_FUNC
