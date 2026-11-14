from datetime import date, datetime, timedelta


def ensure_upcoming_sunday_services(weeks=4, name="Sunday Service", start_time="10:00", location=""):
    """Ensure upcoming Sunday Service records exist (idempotent).

    Safe to call frequently (e.g. from list views); it only performs a few get_or_create lookups.
    """
    from .models import Service

    weeks = max(1, int(weeks))
    try:
        st = start_time if hasattr(start_time, "hour") else datetime.strptime(str(start_time), "%H:%M").time()
    except Exception:
        st = datetime.strptime("10:00", "%H:%M").time()

    today = date.today()
    days_ahead = (6 - today.weekday()) % 7  # 0=Mon..6=Sun; include today if Sunday
    first = today + timedelta(days=days_ahead)

    created = 0
    for i in range(weeks):
        d = first + timedelta(weeks=i)
        _, was_created = Service.objects.get_or_create(
            date=d,
            name=name,
            defaults={
                "start_time": st,
                "location": location or "",
            },
        )
        if was_created:
            created += 1
    return created
