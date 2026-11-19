import json
from urllib import request as urlrequest

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Notification

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'
PUSH_BATCH_SIZE = 100
PUSH_TIMEOUT = 8


def check_fellowship_reminder():
    """Lazily send Thursday fellowship reminder when any member opens the app.

    Fires from 12:30 PM (30 min before the 1 PM fellowship) on Thursdays.
    Called from portal/notifications views so the first member to open the app
    triggers the reminder for everyone. Cron can also fire it at 12:30 PM.
    """
    try:
        now = timezone.localtime()
        if now.weekday() != 3:  # Not Thursday (Mon=0, Thu=3)
            return
        if now.hour < 12 or (now.hour == 12 and now.minute < 30):  # Before 12:30 PM
            return
        # Already sent today?
        already_sent = Notification.objects.filter(
            kind='fellowship_reminder',
            created_at__date=now.date(),
        ).exists()
        if already_sent:
            return
        # Send the reminder (30 minutes before the 1 PM fellowship)
        broadcast(
            title='Thursday Fellowship in 30 Minutes',
            message='Reminder: Thursday fellowship starts at 1:00 PM (in 30 minutes). Please get ready and join us for a time of worship, word and fellowship. See you there!',
            kind='fellowship_reminder',
        )
    except Exception:
        pass  # Never block the API response


def broadcast(title, message, kind='', url=''):
    """Create an in-app notification for every active member and push it to their devices."""
    User = get_user_model()
    users = list(User.objects.filter(is_active=True).only('id'))
    if users:
        Notification.objects.bulk_create(
            [Notification(user=u, title=title, message=message, kind=kind) for u in users],
            batch_size=200,
        )
    _push_expo(title, message, kind, url)


def notify_user(user, message, title='Message from FBMI', kind='message', url=''):
    """Create an in-app notification for a single user and push it to their devices."""
    if not user:
        return
    Notification.objects.create(user=user, title=title[:200], message=message, kind=kind)
    _push_expo_to_user(user, title, message, kind, url)


def _push_expo_to_user(user, title, message, kind='', url=''):
    """Push notification to a specific user's registered devices only."""
    from .models import DeviceToken

    tokens = list(DeviceToken.objects.filter(user=user).values_list('token', flat=True))
    if not tokens:
        return

    data = {'kind': kind}
    if url:
        data['url'] = url

    messages = [
        {
            'to': token,
            'title': (title or 'New update from FBMI')[:120],
            'body': (message or '')[:180],
            'sound': 'default',
            'priority': 'high',
            'channelId': 'updates',
            'data': data,
        }
        for token in tokens
    ]

    stale_tokens = []
    for start in range(0, len(messages), PUSH_BATCH_SIZE):
        batch = messages[start:start + PUSH_BATCH_SIZE]
        body = json.dumps(batch).encode('utf-8')
        req = urlrequest.Request(
            EXPO_PUSH_URL,
            data=body,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        try:
            raw = urlrequest.urlopen(req, timeout=PUSH_TIMEOUT).read()
            payload = json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            continue

        for ticket, msg in zip(payload.get('data', []), batch):
            if not isinstance(ticket, dict) or ticket.get('status') != 'error':
                continue
            details = ticket.get('details') or {}
            if details.get('error') == 'DeviceNotRegistered':
                stale_tokens.append(msg['to'])

    if stale_tokens:
        DeviceToken.objects.filter(token__in=stale_tokens).delete()


def _push_expo(title, message, kind, url=''):
    from .models import DeviceToken

    tokens = list(DeviceToken.objects.values_list('token', flat=True))
    if not tokens:
        return

    data = {'kind': kind}
    if url:
        data['url'] = url

    messages = [
        {
            'to': token,
            'title': (title or 'New update from FBMI')[:120],
            'body': (message or '')[:180],
            'sound': 'default',
            'priority': 'high',
            'channelId': 'updates',
            'data': data,
        }
        for token in tokens
    ]

    stale_tokens = []
    for start in range(0, len(messages), PUSH_BATCH_SIZE):
        batch = messages[start:start + PUSH_BATCH_SIZE]
        body = json.dumps(batch).encode('utf-8')
        req = urlrequest.Request(
            EXPO_PUSH_URL,
            data=body,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        try:
            raw = urlrequest.urlopen(req, timeout=PUSH_TIMEOUT).read()
            payload = json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            # A push failure must never block posting content.
            continue

        for ticket, message in zip(payload.get('data', []), batch):
            if not isinstance(ticket, dict) or ticket.get('status') != 'error':
                continue
            details = ticket.get('details') or {}
            if details.get('error') == 'DeviceNotRegistered':
                stale_tokens.append(message['to'])

    if stale_tokens:
        DeviceToken.objects.filter(token__in=stale_tokens).delete()
