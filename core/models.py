from django.db import models


class ChurchSetting(models.Model):
    church_name = models.CharField(max_length=200, default='Fruitful Brethren Ministry International')
    short_name = models.CharField(max_length=20, default='F.B.M.I.')
    logo = models.ImageField(upload_to='church/', blank=True, null=True)
    favicon = models.ImageField(upload_to='church/', blank=True, null=True)
    hero_image = models.ImageField(upload_to='church/', blank=True, null=True, help_text='Homepage hero background (1920x1080 recommended)')
    events_image = models.ImageField(upload_to='church/', blank=True, null=True, help_text='Events section image')
    sermons_image = models.ImageField(upload_to='church/', blank=True, null=True, help_text='Sermons section image')
    cta_image = models.ImageField(upload_to='church/', blank=True, null=True, help_text='Call to action section image')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    currency = models.CharField(max_length=10, default='KES')
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    primary_color = models.CharField(max_length=7, default='#6794A6')
    secondary_color = models.CharField(max_length=7, default='#546280')
    accent_color = models.CharField(max_length=7, default='#BF2D30')
    gold_color = models.CharField(max_length=7, default='#BAA883')
    service_times = models.TextField(blank=True, help_text='One per line')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Church Setting'
        verbose_name_plural = 'Church Settings'

    def __str__(self):
        return self.church_name

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Notification(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user}"
