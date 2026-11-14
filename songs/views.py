from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.views import ContentWriteMixin
from services.utils import get_next_sunday_service, set_songs_for_service
from .models import Song


class SongListView(LoginRequiredMixin, ListView):
    model = Song
    template_name = 'songs/song_list.html'
    context_object_name = 'songs'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category', '').strip()
        search = self.request.GET.get('search', '').strip()
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(author__icontains=search) | Q(lyrics__icontains=search) | Q(chord_progression__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.request.GET.get('category', '')
        context['search'] = self.request.GET.get('search', '')
        context['categories'] = Song.CATEGORY_CHOICES
        sunday_service = None
        selected_ids = set()
        try:
            sunday_service = get_next_sunday_service()
            if sunday_service:
                selected_ids = set(sunday_service.setlist.values_list('song_id', flat=True))
        except Exception:
            sunday_service = None
            selected_ids = set()
        context['sunday_service'] = sunday_service
        context['selected_song_ids'] = selected_ids
        # IDs on current page, to preserve off-page selections when saving
        page_obj = context.get('songs') or []
        context['page_song_ids'] = {s.id for s in page_obj}
        return context

    def post(self, request, *args, **kwargs):
        if not getattr(request.user, 'can_manage_content', False):
            return redirect('songs:song_list')
        try:
            service = get_next_sunday_service()
            if service:
                song_ids = request.POST.getlist('songs_for_sunday')
                set_songs_for_service(service, song_ids)
                messages.success(request, f'Songs for {service.name} ({service.date}) updated.')
            else:
                messages.error(request, 'Could not find the next Sunday service.')
        except Exception as e:
            messages.error(request, f'Could not update songs: {e}')
        # preserve filters in redirect
        params = request.GET.urlencode()
        url = reverse_lazy('songs:song_list')
        return redirect(f"{url}?{params}" if params else url)


class SongDetailView(LoginRequiredMixin, DetailView):
    model = Song
    template_name = 'songs/song_detail.html'
    context_object_name = 'song'


class SongCreateView(LoginRequiredMixin, ContentWriteMixin, CreateView):
    model = Song
    template_name = 'songs/song_form.html'
    fields = ['title', 'category', 'lyrics', 'chord_progression', 'author', 'scripture', 'key', 'tempo', 'youtube_url']
    success_url = reverse_lazy('songs:song_list')

    def form_valid(self, form):
        messages.success(self.request, 'Song posted successfully.')
        return super().form_valid(form)


class SongUpdateView(LoginRequiredMixin, ContentWriteMixin, UpdateView):
    model = Song
    template_name = 'songs/song_form.html'
    fields = ['title', 'category', 'lyrics', 'chord_progression', 'author', 'scripture', 'key', 'tempo', 'youtube_url']
    success_url = reverse_lazy('songs:song_list')

    def form_valid(self, form):
        messages.success(self.request, 'Song updated successfully.')
        return super().form_valid(form)


class SongDeleteView(LoginRequiredMixin, ContentWriteMixin, DeleteView):
    model = Song
    template_name = 'songs/song_confirm_delete.html'
    success_url = reverse_lazy('songs:song_list')

    def form_valid(self, form):
        messages.success(self.request, 'Song deleted successfully.')
        return super().form_valid(form)
