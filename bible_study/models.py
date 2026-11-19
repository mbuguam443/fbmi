from django.db import models


class BibleStudyNote(models.Model):
    title = models.CharField(max_length=300)
    bible_verse = models.CharField(max_length=200)
    study_date = models.DateField()
    teacher = models.CharField(max_length=200, blank=True)
    series = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    key_points = models.TextField(blank=True)
    prayer_points = models.TextField(blank=True)
    discussion_questions = models.TextField(blank=True)
    youtube_url = models.URLField(blank=True, help_text='Link to a video teaching (YouTube, etc.)')
    audio_file = models.FileField(upload_to='bible_study/audio/', blank=True, null=True, help_text='Audio recording of the teaching')
    video_file = models.FileField(upload_to='bible_study/video/', blank=True, null=True, help_text='Video file of the teaching')
    pdf_file = models.FileField(upload_to='bible_study/pdf/', blank=True, null=True, help_text='PDF study guide or notes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-study_date']

    def __str__(self):
        return f"{self.title} - {self.bible_verse}"
