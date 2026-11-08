from django.contrib import admin

from .models import Service, ServiceSong


class ServiceSongInline(admin.TabularInline):
    model = ServiceSong
    extra = 1
    autocomplete_fields = ['song']
    ordering = ['order']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'start_time', 'end_time', 'location', 'preacher', 'theme']
    list_filter = ['date', 'location']
    search_fields = ['name', 'preacher', 'theme', 'bible_verse']
    inlines = [ServiceSongInline]
    date_hierarchy = 'date'


@admin.register(ServiceSong)
class ServiceSongAdmin(admin.ModelAdmin):
    list_display = ['service', 'order', 'section', 'song', 'notes']
    list_filter = ['section', 'service__date']
    search_fields = ['song__title', 'service__name']
    autocomplete_fields = ['service', 'song']
    ordering = ['service', 'order']