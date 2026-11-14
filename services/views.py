from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from accounts.views import ContentWriteMixin
from .models import Service, ServiceSong
from .utils import ensure_upcoming_sunday_services


ServiceSongFormSet = inlineformset_factory(
    Service,
    ServiceSong,
    fields=['order', 'section', 'song', 'notes'],
    extra=10,
    can_delete=True,
)


class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 20

    def get_queryset(self):
        try:
            ensure_upcoming_sunday_services()
        except Exception:
            pass
        return super().get_queryset()


class ServiceCreateView(LoginRequiredMixin, ContentWriteMixin, CreateView):
    model = Service
    template_name = 'services/service_form.html'
    fields = ['name', 'date', 'start_time', 'end_time', 'location', 'preacher', 'theme', 'bible_verse', 'notes']
    success_url = reverse_lazy('services:service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['song_formset'] = ServiceSongFormSet(self.request.POST, instance=self.object)
        else:
            context['song_formset'] = ServiceSongFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        song_formset = context['song_formset']
        if song_formset.is_valid():
            self.object = form.save()
            song_formset.instance = self.object
            song_formset.save()
            messages.success(self.request, 'Service created successfully.')
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))


class ServiceUpdateView(LoginRequiredMixin, ContentWriteMixin, UpdateView):
    model = Service
    template_name = 'services/service_form.html'
    fields = ['name', 'date', 'start_time', 'end_time', 'location', 'preacher', 'theme', 'bible_verse', 'notes']
    success_url = reverse_lazy('services:service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['song_formset'] = ServiceSongFormSet(self.request.POST, instance=self.object)
        else:
            context['song_formset'] = ServiceSongFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        song_formset = context['song_formset']
        if song_formset.is_valid():
            self.object = form.save()
            song_formset.instance = self.object
            song_formset.save()
            messages.success(self.request, 'Service updated successfully.')
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))


class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'


class ServiceDeleteView(LoginRequiredMixin, ContentWriteMixin, DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'
    success_url = reverse_lazy('services:service_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Service deleted successfully.')
        return super().delete(request, *args, **kwargs)
