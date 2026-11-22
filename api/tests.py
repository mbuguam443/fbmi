import json
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from api.models import ApiToken, DeviceToken
from api.notify import _push_expo
from attendance.models import Attendance
from attendance.qr import make_service_token, make_sunday_token
from communication.models import Announcement
from core.models import Notification
from members.models import Member
from services.models import Service


class RealtimeNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.member = User.objects.create_user(username='member1', password='secret123')
        self.pending = User.objects.create_user(username='pending1', password='secret123', is_active=False)

    def test_new_active_post_notifies_active_members_only(self):
        Announcement.objects.create(title='Sunday update', message='Hello church', is_active=True)

        self.assertEqual(self.member.notifications.count(), 1)
        self.assertEqual(self.pending.notifications.count(), 0)
        notification = self.member.notifications.first()
        self.assertEqual(notification.kind, 'announcements')
        self.assertEqual(notification.title, 'Sunday update')

    def test_draft_post_notifies_when_it_is_published(self):
        announcement = Announcement.objects.create(title='Draft', message='Later', is_active=False)
        self.assertEqual(self.member.notifications.count(), 0)

        announcement.is_active = True
        announcement.save()
        self.assertEqual(self.member.notifications.count(), 1)

    def test_editing_a_published_post_does_not_duplicate(self):
        announcement = Announcement.objects.create(title='Update', message='Hi', is_active=True)
        announcement.message = 'Updated wording'
        announcement.save()
        self.assertEqual(self.member.notifications.count(), 1)

    def test_notifications_since_returns_only_newer_posts(self):
        first = Notification.objects.create(
            user=self.member, title='One', message='first', kind='announcements'
        )
        Notification.objects.create(user=self.member, title='Two', message='second', kind='events')
        token = ApiToken.create_for_user(self.member)

        response = self.client.get(
            f'/api/notifications/?since={first.id}',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([item['title'] for item in data['results']], ['Two'])
        self.assertEqual(data['unread_count'], 2)
        self.assertEqual(data['latest_id'], first.id + 1)
        self.assertEqual(data['results'][0]['url'], '/list/events')

    @mock.patch('api.notify.urlrequest.urlopen')
    def test_push_payload_uses_updates_channel_and_drops_stale_tokens(self, urlopen):
        DeviceToken.objects.create(user=self.member, token='ExponentPushToken[good]', platform='android')
        DeviceToken.objects.create(user=self.member, token='ExponentPushToken[stale]', platform='android')

        response = mock.MagicMock()
        response.read.return_value = json.dumps(
            {
                'data': [
                    {'status': 'ok'},
                    {'status': 'error', 'details': {'error': 'DeviceNotRegistered'}},
                ]
            }
        ).encode('utf-8')
        urlopen.return_value = response

        _push_expo('New post', 'A new announcement was posted', 'announcements', '/list/announcements')

        request = urlopen.call_args.args[0]
        sent = json.loads(request.data.decode('utf-8'))
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0]['channelId'], 'updates')
        self.assertEqual(sent[0]['data'], {'kind': 'announcements', 'url': '/list/announcements'})
        self.assertEqual(
            list(DeviceToken.objects.values_list('token', flat=True)),
            ['ExponentPushToken[good]'],
        )


class AttendanceQRTests(TestCase):
    """The permanent Sunday QR must work on Sundays without reprinting."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='qr_member', password='secret123')
        self.member = Member.objects.create(
            user=self.user, first_name='Test', last_name='Member', gender='male'
        )
        self.api_token = ApiToken.create_for_user(self.user)
        self.sunday = date(2026, 11, 22)  # a Sunday
        self.service = Service.objects.create(
            name='Sunday Service', date=self.sunday, start_time='10:00'
        )

    def _scan(self, qr_token):
        return self.client.post(
            '/api/attendance/scan/',
            data=json.dumps({'token': qr_token}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.api_token.key}',
        )

    def test_permanent_token_never_changes(self):
        self.assertEqual(make_sunday_token(), make_sunday_token())

    @mock.patch('django.utils.timezone.localdate')
    def test_permanent_qr_checks_into_todays_sunday_service(self, localdate):
        localdate.return_value = self.sunday
        response = self._scan(make_sunday_token())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['created'])
        self.assertEqual(data['service']['id'], self.service.id)
        self.assertEqual(
            Attendance.objects.filter(member=self.member, service=self.service).count(), 1
        )

    @mock.patch('django.utils.timezone.localdate')
    def test_permanent_qr_is_safe_to_rescan(self, localdate):
        localdate.return_value = self.sunday
        self._scan(make_sunday_token())
        response = self._scan(make_sunday_token())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['created'])
        self.assertEqual(Attendance.objects.filter(member=self.member).count(), 1)

    @mock.patch('django.utils.timezone.localdate')
    def test_permanent_qr_rejected_on_non_sundays(self, localdate):
        localdate.return_value = self.sunday - timedelta(days=1)
        response = self._scan(make_sunday_token())
        self.assertEqual(response.status_code, 400)
        self.assertIn('Sundays only', response.json()['error'])
        self.assertEqual(Attendance.objects.count(), 0)

    @mock.patch('django.utils.timezone.localdate')
    def test_legacy_per_service_qr_still_works(self, localdate):
        localdate.return_value = self.sunday
        response = self._scan(make_service_token(self.service.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['service']['id'], self.service.id)
