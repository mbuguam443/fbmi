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


def get_next_sunday_service():
    """Return the next upcoming Sunday service (today if today is Sunday), ensuring it exists."""
    from .models import Service

    ensure_upcoming_sunday_services(weeks=2)
    today = date.today()
    days_ahead = (6 - today.weekday()) % 7
    sunday = today + timedelta(days=days_ahead)
    service = (
        Service.objects.filter(date=sunday, name="Sunday Service").first()
        or Service.objects.filter(date=sunday).order_by("start_time").first()
    )
    return service


def set_songs_for_service(service, song_ids):
    """Sync selected song IDs into a service setlist.

    Adds selected songs not present and removes unselected ones. New songs are appended,
    ordered/grouped by category (praise, worship, others) then title.
    """
    from songs.models import Song
    from .models import ServiceSong

    wanted = [int(sid) for sid in (song_ids or []) if str(sid).isdigit()]
    wanted_set = set(wanted)

    existing = list(ServiceSong.objects.filter(service=service).select_related('song'))
    existing_ids = {item.song_id for item in existing}

    # Remove unselected
    ServiceSong.objects.filter(service=service).exclude(song_id__in=wanted_set).delete()

    # Add newly selected
    to_add_ids = [sid for sid in wanted if sid not in existing_ids]
    if to_add_ids:
        songs = {s.id: s for s in Song.objects.filter(id__in=to_add_ids)}
        # preserve the order they were submitted if meaningful, else group
        category_rank = {'praise': 0, 'worship': 1, 'hymn': 2, 'chorus': 3, 'gospel': 4, 'contemporary': 5}
        ordered = sorted(
            [songs[sid] for sid in to_add_ids if sid in songs],
            key=lambda s: (category_rank.get(getattr(s, 'category', ''), 9), s.title.lower()),
        )
        # determine starting order
        current_max = 0
        for item in ServiceSong.objects.filter(service=service):
            if item.order and item.order > current_max:
                current_max = item.order
        # also consider remaining count
        base = max(current_max, ServiceSong.objects.filter(service=service).count())
        # avoid unique_together conflicts on order: use next integers
        used_orders = set(ServiceSong.objects.filter(service=service).values_list('order', flat=True))
        next_order = base + 1
        for song in ordered:
            while next_order in used_orders:
                next_order += 1
            section = 'praise' if song.category == 'praise' else ('worship' if song.category == 'worship' else 'special')
            ServiceSong.objects.create(service=service, song=song, order=next_order, section=section)
            used_orders.add(next_order)
            next_order += 1

    # Normalize orders to be sequential 1..n for cleanliness
    remaining = list(ServiceSong.objects.filter(service=service).select_related('song').order_by('order', 'id'))
    for idx, item in enumerate(remaining, start=1):
        if item.order != idx:
            # avoid unique collision by two-step not necessary usually since sequential; but be safe
            ServiceSong.objects.filter(pk=item.pk).update(order=idx)
