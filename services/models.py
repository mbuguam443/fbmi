from django.db import models
from members.models import Member


class Service(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    preacher = models.CharField(max_length=200, blank=True)
    theme = models.CharField(max_length=200, blank=True)
    bible_verse = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.name} - {self.date}"


class ServiceSong(models.Model):
    SECTION_CHOICES = [
        ('opening', 'Opening'),
        ('praise', 'Praise'),
        ('worship', 'Worship'),
        ('offering', 'Offering'),
        ('special', 'Special / Item'),
        ('closing', 'Closing'),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='setlist')
    song = models.ForeignKey('songs.Song', on_delete=models.CASCADE, related_name='service_appearances')
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first.')
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='worship')
    notes = models.CharField(max_length=200, blank=True, help_text='Optional note (e.g. key change, leader).')

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['service', 'order']

    def __str__(self):
        return f"{self.service} — {self.order}. {self.song.title}"
