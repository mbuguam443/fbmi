from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from accounts.views import ContentWriteMixin
from .models import PrayerRequest


class PrayerRequestListView(LoginRequiredMixin, ListView):
    model = PrayerRequest
    template_name = 'prayer/prayer_list.html'
    context_object_name = 'prayer_requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('member', 'user')
        status = self.request.GET.get('status', '').strip()
        category = self.request.GET.get('category', '').strip()
        search = self.request.GET.get('search', '').strip()

        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(request__icontains=search)
                | Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['search'] = self.request.GET.get('search', '')
        context['status_choices'] = PrayerRequest.STATUS_CHOICES
        context['category_choices'] = PrayerRequest.CATEGORY_CHOICES
        context['new_count'] = PrayerRequest.objects.filter(status='new').count()
        context['praying_count'] = PrayerRequest.objects.filter(status='praying').count()
        context['answered_count'] = PrayerRequest.objects.filter(status='answered').count()
        context['pending_count'] = PrayerRequest.objects.filter(status='pending').count()
        return context


class PrayerRequestDetailView(LoginRequiredMixin, DetailView):
    model = PrayerRequest
    template_name = 'prayer/prayer_detail.html'
    context_object_name = 'prayer_request'

    def post(self, request, *args, **kwargs):
        """Quick pastor response: update status and send encouragement."""
        self.object = self.get_object()
        if not request.user.can_manage_content:
            messages.error(request, 'You do not have permission to respond to prayer requests.')
            return redirect('prayer:prayer-request-detail', pk=self.object.pk)

        from .models import PrayerRequest as PR
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}

        new_status = data.get('status', '').strip()
        response_text = (data.get('response', '') or '').strip()

        if new_status and new_status in dict(PR.STATUS_CHOICES):
            self.object.status = new_status
        if response_text:
            self.object.pastor_response = response_text
            self.object.response_date = timezone.now()
            self.object.response_by = request.user
        self.object.save()

        # Notify the member in-app about the pastor's response
        if response_text or new_status:
            try:
                from core.models import Notification
                from api.notify import notify_user
                target_user = self.object.user or (self.object.member.user if self.object.member and hasattr(self.object.member, 'user') else None)
                if target_user:
                    status_msg = f'status: {self.object.get_status_display()}' if new_status else ''
                    msg = f'The pastor has responded to your prayer request "{self.object.title}"'
                    if status_msg:
                        msg += f' ({status_msg})'
                    notify_user(target_user, msg, kind='prayer', url=f'/read/prayers/{self.object.pk}')
            except Exception:
                pass

        messages.success(request, 'Prayer request updated successfully.')
        return redirect('prayer:prayer-request-detail', pk=self.object.pk)


class PrayerRequestCreateView(LoginRequiredMixin, CreateView):
    model = PrayerRequest
    template_name = 'prayer/prayer_form.html'
    fields = ['member', 'title', 'request', 'category', 'is_confidential']
    success_url = reverse_lazy('prayer:prayer-request-list')

    def form_valid(self, form):
        messages.success(self.request, 'Prayer request submitted successfully.')
        return super().form_valid(form)


class PrayerRequestUpdateView(LoginRequiredMixin, ContentWriteMixin, UpdateView):
    model = PrayerRequest
    template_name = 'prayer/prayer_form.html'
    fields = ['member', 'title', 'request', 'category', 'status', 'assigned_to', 'notes', 'is_confidential', 'pastor_response']
    success_url = reverse_lazy('prayer:prayer-request-list')

    def form_valid(self, form):
        if form.instance.pastor_response and form.instance.pastor_response != self.get_object().pastor_response:
            form.instance.response_date = timezone.now()
            form.instance.response_by = self.request.user
        messages.success(self.request, 'Prayer request updated successfully.')
        return super().form_valid(form)


class PrayerRequestDeleteView(LoginRequiredMixin, ContentWriteMixin, DeleteView):
    model = PrayerRequest
    template_name = 'prayer/prayer_confirm_delete.html'
    context_object_name = 'prayer_request'
    success_url = reverse_lazy('prayer:prayer-request-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Prayer request deleted successfully.')
        return super().delete(request, *args, **kwargs)
