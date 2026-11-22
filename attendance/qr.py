"""Shared helpers for attendance QR codes.

Two token shapes are supported so staff can print one permanent QR for every
Sunday while older, per-service codes keep working:

* ``{'scope': 'sunday'}`` - universal Sunday code. It contains no service id
  and no timestamp, so it never changes. The service is resolved at scan time.
* ``{'s': <service id>}`` - legacy per-service code (kept for compatibility).
"""
from django.core import signing
from django.utils import timezone

QR_SALT = 'attendance-qr'
SUNDAY_SCOPE = 'sunday'


def _signer():
    return signing.Signer(salt=QR_SALT)


def make_service_token(service_id):
    """Signed token for one specific service (legacy behaviour)."""
    return _signer().sign_object({'s': int(service_id)})


def make_sunday_token():
    """Permanent signed token that works for every Sunday service."""
    return _signer().sign_object({'scope': SUNDAY_SCOPE})


def decode_token(token):
    """Return the unsigned payload dict, or ``None`` when the token is invalid."""
    if not token:
        return None
    try:
        payload = _signer().unsign_object(str(token).strip())
    except (signing.BadSignature, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def is_sunday_token(payload):
    return isinstance(payload, dict) and payload.get('scope') == SUNDAY_SCOPE


def service_id_from_token(payload):
    if not isinstance(payload, dict) or 's' not in payload:
        return None
    try:
        return int(payload['s'])
    except (ValueError, TypeError):
        return None


def resolve_sunday_service(today=None):
    """Return the service today's universal Sunday QR checks members into.

    Selection rule (documented so staff know what to expect):

    1. Prefer a service named exactly "Sunday Service".
    2. Otherwise a service whose name contains "sunday".
    3. Otherwise the earliest service scheduled today.

    Returns ``None`` on any day other than Sunday. If a Sunday has no service
    records at all, the canonical "Sunday Service" is created so the permanent
    QR never fails simply because nobody opened the Services page first.
    """
    from services.models import Service

    today = today or timezone.localdate()
    if today.weekday() != 6:  # Monday=0 ... Sunday=6
        return None

    def pick():
        qs = Service.objects.filter(date=today)
        return (
            qs.filter(name__iexact='Sunday Service').order_by('start_time', 'id').first()
            or qs.filter(name__icontains='sunday').order_by('start_time', 'id').first()
            or qs.order_by('start_time', 'id').first()
        )

    service = pick()
    if service is None:
        from services.utils import ensure_upcoming_sunday_services

        ensure_upcoming_sunday_services(weeks=1)
        service = pick()
    return service
