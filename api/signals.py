from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from bible_study.models import BibleStudyNote
from communication.models import Announcement
from events.models import Event
from sermons.models import Sermon
from services.models import Service
from songs.models import Song

from .notify import broadcast


def _remember_active_state(sender, instance):
    """Store the previous ``is_active`` value so post_save can detect publishing."""
    instance._was_active = False
    if instance.pk:
        instance._was_active = bool(
            sender.objects.filter(pk=instance.pk).values_list('is_active', flat=True).first()
        )


@receiver(pre_save, sender=Announcement, dispatch_uid='api.announcement_pre_save')
def _announcement_pre_save(sender, instance, **kwargs):
    _remember_active_state(sender, instance)


@receiver(pre_save, sender=Event, dispatch_uid='api.event_pre_save')
def _event_pre_save(sender, instance, **kwargs):
    _remember_active_state(sender, instance)


@receiver(pre_save, sender=BibleStudyNote, dispatch_uid='api.bible_study_pre_save')
def _bible_study_pre_save(sender, instance, **kwargs):
    _remember_active_state(sender, instance)


def _just_published(instance, created):
    """True when a post is newly created or toggled from inactive to active."""
    if not getattr(instance, 'is_active', True):
        return False
    if created:
        return True
    return not getattr(instance, '_was_active', True)


@receiver(post_save, sender=Announcement, dispatch_uid='api.announcement_post_save')
def on_announcement(sender, instance, created, **kwargs):
    if _just_published(instance, created):
        broadcast(instance.title, instance.message, 'announcements', '/list/announcements')


@receiver(post_save, sender=Event, dispatch_uid='api.event_post_save')
def on_event(sender, instance, created, **kwargs):
    if _just_published(instance, created):
        broadcast(
            instance.name,
            instance.description or 'A new church event is coming up.',
            'events',
            '/list/events',
        )


@receiver(post_save, sender=Sermon, dispatch_uid='api.sermon_post_save')
def on_sermon(sender, instance, created, **kwargs):
    if not created:
        return
    is_devotion = getattr(instance, 'category', '') == 'devotion'
    kind = 'devotions' if is_devotion else 'sermons'
    broadcast(
        instance.title,
        instance.description or 'A new message is ready to read.',
        kind,
        f'/read/{kind}/{instance.pk}',
    )


@receiver(post_save, sender=BibleStudyNote, dispatch_uid='api.bible_study_post_save')
def on_bible_study(sender, instance, created, **kwargs):
    if _just_published(instance, created):
        broadcast(
            instance.title,
            instance.bible_verse or 'New Bible study notes are ready.',
            'bible-study',
            f'/read/bible-study/{instance.pk}',
        )


@receiver(post_save, sender=Song, dispatch_uid='api.song_post_save')
def on_song(sender, instance, created, **kwargs):
    if created:
        broadcast(
            instance.title,
            'New lyrics are in Songs & Hymns.',
            'songs',
            f'/read/songs/{instance.pk}',
        )


@receiver(post_save, sender=Service, dispatch_uid='api.service_post_save')
def on_service(sender, instance, created, **kwargs):
    if created:
        broadcast(
            instance.name,
            'A service is on the calendar. Check in when you arrive.',
            'attendance',
            '/list/attendance',
        )
