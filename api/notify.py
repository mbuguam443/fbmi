import json
from urllib import request as urlrequest

from django.contrib.auth import get_user_model

from core.models import Notification

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'
PUSH_BATCH_SIZE = 100
PUSH_TIMEOUT = 8


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
