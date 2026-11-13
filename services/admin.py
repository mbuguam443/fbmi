from django.contrib import admin

from .models import Service, ServiceSong


class ServiceSongInline(admin.TabularInline):
    model = ServiceSong
    extra = 1
    autocomplete_fields = ['song']
    ordering = ['order']
    fields = ['order', 'section', 'song', 'song_category', 'notes']
    readonly_fields = ['song_category']

    @admin.display(description='Song type')
    def song_category(self, obj):
        if not obj or not obj.pk:
            return '-'
        return obj.song.get_category_display()


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'start_time', 'end_time', 'location', 'preacher', 'theme', 'song_count']
    list_filter = ['date', 'location']
    search_fields = ['name', 'preacher', 'theme', 'bible_verse']
    inlines = [ServiceSongInline]
    date_hierarchy = 'date'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('setlist__song')

    @admin.display(description='Songs')
    def song_count(self, obj):
        return obj.setlist.count()


@admin.register(ServiceSong)
class ServiceSongAdmin(admin.ModelAdmin):
    list_display = ['service', 'order', 'section', 'song', 'notes']
    list_filter = ['section', 'service__date']
    search_fields = ['song__title', 'service__name']
    autocomplete_fields = ['service', 'song']
    ordering = ['service', 'order']