from django.db import models


class Sermon(models.Model):
    title = models.CharField(max_length=300)
    speaker = models.CharField(max_length=200)
    date = models.DateField()
    bible_verse = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    sermon_notes = models.TextField(blank=True)
    audio_file = models.FileField(upload_to='sermons/audio/', blank=True, null=True)
    video_file = models.FileField(upload_to='sermons/video/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='sermons/pdf/', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.speaker}"
