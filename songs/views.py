from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
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
            queryset = queryset.filter(title__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.request.GET.get('category', '')
        context['search'] = self.request.GET.get('search', '')
        context['categories'] = Song.CATEGORY_CHOICES
        return context


class SongDetailView(LoginRequiredMixin, DetailView):
    model = Song
    template_name = 'songs/song_detail.html'
    context_object_name = 'song'
