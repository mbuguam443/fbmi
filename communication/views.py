from django.contrib import messages as django_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from accounts.views import ContentWriteMixin
from .models import Announcement, DirectMessage


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'communication/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        target = self.request.GET.get('target', '')
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(message__icontains=search)
        if target:
            queryset = queryset.filter(target_audience__iexact=target)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['target'] = self.request.GET.get('target', '')
        context['target_choices'] = Announcement.TARGET_CHOICES
        return context


class AnnouncementCreateView(LoginRequiredMixin, ContentWriteMixin, CreateView):
    model = Announcement
    template_name = 'communication/announcement_form.html'
    fields = ['title', 'message', 'target_audience', 'expiry_date', 'is_active']
    success_url = reverse_lazy('communication:announcement_list')

    def form_valid(self, form):
        django_messages.success(self.request, 'Announcement created successfully.')
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, ContentWriteMixin, UpdateView):
    model = Announcement
    template_name = 'communication/announcement_form.html'
    fields = ['title', 'message', 'target_audience', 'expiry_date', 'is_active']
    success_url = reverse_lazy('communication:announcement_list')

    def form_valid(self, form):
        django_messages.success(self.request, 'Announcement updated successfully.')
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, ContentWriteMixin, DeleteView):
    model = Announcement
    template_name = 'communication/announcement_confirm_delete.html'
    success_url = reverse_lazy('communication:announcement_list')

    def delete(self, request, *args, **kwargs):
        django_messages.success(request, 'Announcement deleted successfully.')
        return super().delete(request, *args, **kwargs)


class DirectMessageListView(LoginRequiredMixin, ListView):
    """List of messages sent to members."""
    model = DirectMessage
    template_name = 'communication/message_list.html'
    context_object_name = 'direct_messages'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('member', 'sender')
        search = self.request.GET.get('search', '').strip()
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(message__icontains=search)
                | Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['total_sent'] = DirectMessage.objects.count()
        context['unread_count'] = DirectMessage.objects.filter(is_read=False).count()
        return context


class DirectMessageCreateView(LoginRequiredMixin, ContentWriteMixin, TemplateView):
    """Send a message to an individual member (they get an in-app alert + push notification)."""
    template_name = 'communication/message_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from members.models import Member
        context['members'] = Member.objects.filter(
            user__isnull=False, user__is_active=True
        ).select_related('user').order_by('first_name', 'last_name')
        context['recent_messages'] = DirectMessage.objects.select_related('member')[:5]
        return context

    def post(self, request, *args, **kwargs):
        from members.models import Member
        from api.notify import notify_user

        member_id = request.POST.get('member', '').strip()
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()

        if not member_id:
            django_messages.error(request, 'Please select a member.')
            return redirect('communication:message_create')
        if not title:
            django_messages.error(request, 'Please enter a title.')
            return redirect('communication:message_create')
        if not message:
            django_messages.error(request, 'Please enter a message.')
            return redirect('communication:message_create')

        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            django_messages.error(request, 'Member not found.')
            return redirect('communication:message_create')

        dm = DirectMessage.objects.create(
            sender=request.user,
            member=member,
            title=title[:200],
            message=message,
        )

        # Send in-app notification + push to the member's devices
        target_user = getattr(member, 'user', None)
        if target_user and target_user.is_active:
            try:
                notify_user(
                    target_user,
                    message,
                    title=f'Message from {request.user.get_full_name() or request.user.username}',
                    kind='message',
                    url='/notifications/',
                )
            except Exception:
                pass

        django_messages.success(request, f'Message sent to {member.first_name} {member.last_name}.')
        return redirect('communication:message_list')
