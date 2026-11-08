import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from api.models import ApiToken, DeviceToken
from api.notify import _push_expo
from communication.models import Announcement
from core.models import Notification


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
