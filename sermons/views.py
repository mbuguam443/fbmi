from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from .models import Sermon


class SermonListView(LoginRequiredMixin, ListView):
    model = Sermon
    template_name = 'sermons/sermon_list.html'
    context_object_name = 'sermons'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        category = self.request.GET.get('category', '')
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(speaker__icontains=search)
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['category'] = self.request.GET.get('category', '')
        context['categories'] = [(c, c) for c in Sermon.objects.values_list('category', flat=True).distinct() if c]
        return context


class SermonCreateView(LoginRequiredMixin, CreateView):
    model = Sermon
    template_name = 'sermons/sermon_form.html'
    fields = ['title', 'speaker', 'date', 'bible_verse', 'description', 'sermon_notes', 'audio_file', 'video_file', 'pdf_file', 'category']
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sermon created successfully.')
        return super().form_valid(form)


class SermonUpdateView(LoginRequiredMixin, UpdateView):
    model = Sermon
    template_name = 'sermons/sermon_form.html'
    fields = ['title', 'speaker', 'date', 'bible_verse', 'description', 'sermon_notes', 'audio_file', 'video_file', 'pdf_file', 'category']
    success_url = reverse_lazy('sermons:sermon_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sermon updated successfully.')
        return super().form_valid(form)


class SermonDetailView(LoginRequiredMixin, DetailView):
    model = Sermon
    template_name = 'sermons/sermon_detail.html'
    context_object_name = 'sermon'


class SermonDeleteView(LoginRequiredMixin, DeleteView):
    model = Sermon
    template_name = 'sermons/sermon_confirm_delete.html'
    success_url = reverse_lazy('sermons:sermon_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Sermon deleted successfully.')
        return super().delete(request, *args, **kwargs)
