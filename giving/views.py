from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView,
)

from .models import Giving


class FinanceAccessMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_finance

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access giving records.')
        return super().handle_no_permission()


class GivingListView(LoginRequiredMixin, FinanceAccessMixin, ListView):
    model = Giving
    template_name = 'giving/giving_list.html'
    context_object_name = 'givings'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('member')
        # Accept both template param names (category/search) and view param names (giving_category/member)
        member = (self.request.GET.get('member', '') or self.request.GET.get('search', '')).strip()
        giving_category = (self.request.GET.get('giving_category', '') or self.request.GET.get('category', '')).strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        payment_method = self.request.GET.get('payment_method', '').strip()

        if member:
            queryset = queryset.filter(
                Q(member__first_name__icontains=member)
                | Q(member__last_name__icontains=member)
                | Q(member__member_number__icontains=member)
            )
        if giving_category:
            queryset = queryset.filter(giving_category=giving_category)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Auto-refresh pending M-Pesa STK payments so dashboard shows current status.
        try:
            from .mpesa import refresh_pending_stk_givings
            pending = queryset.filter(payment_method='mpesa', status='pending').exclude(mpesa_checkout_request_id='')
            if pending.exists():
                refresh_pending_stk_givings(list(pending[:25]))
        except Exception:
            pass
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member_filter'] = self.request.GET.get('member', '') or self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('giving_category', '') or self.request.GET.get('category', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['payment_filter'] = self.request.GET.get('payment_method', '')
        context['category_choices'] = Giving.GIVING_CATEGORIES
        context['payment_choices'] = Giving.PAYMENT_METHODS

        # Analytics: overall stats (all completed giving, not filtered)
        completed = Giving.objects.filter(status='completed')
        agg = completed.aggregate(
            total=Sum('amount'),
            avg=Avg('amount'),
            contributors=Count('member', distinct=True),
        )
        context['total_amount'] = agg['total'] or 0
        context['average_amount'] = round(agg['avg'] or 0, 2)
        context['contributor_count'] = agg['contributors'] or 0

        # This month's total
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_agg = completed.filter(date__gte=month_start.date()).aggregate(total=Sum('amount'))
        context['monthly_total'] = monthly_agg['total'] or 0

        # Filtered total (for table footer when filters are applied)
        filtered_agg = self.object_list.aggregate(total=Sum('amount'))
        context['filtered_total'] = filtered_agg['total'] or 0

        return context


class GivingCreateView(LoginRequiredMixin, FinanceAccessMixin, CreateView):
    model = Giving
    template_name = 'giving/giving_form.html'
    fields = ['member', 'amount', 'giving_category', 'date', 'payment_method', 'reference_number', 'notes']
    success_url = reverse_lazy('giving:giving-list')

    def form_valid(self, form):
        messages.success(self.request, 'Giving record created successfully.')
        return super().form_valid(form)


class GivingUpdateView(LoginRequiredMixin, FinanceAccessMixin, UpdateView):
    model = Giving
    template_name = 'giving/giving_form.html'
    fields = ['member', 'amount', 'giving_category', 'date', 'payment_method', 'reference_number', 'notes']
    success_url = reverse_lazy('giving:giving-list')

    def form_valid(self, form):
        messages.success(self.request, 'Giving record updated successfully.')
        return super().form_valid(form)


class GivingDeleteView(LoginRequiredMixin, FinanceAccessMixin, DeleteView):
    model = Giving
    template_name = 'giving/giving_confirm_delete.html'
    context_object_name = 'giving'
    success_url = reverse_lazy('giving:giving-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Giving record deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(lambda u: u.is_finance)
@require_POST
def giving_refresh_mpesa_status(request, pk):
    giving = get_object_or_404(Giving, pk=pk)
    if giving.payment_method != 'mpesa' or not (giving.mpesa_checkout_request_id or '').strip():
        messages.info(request, 'This giving does not have an M-Pesa STK request to check.')
        return redirect('giving:giving-list')
    try:
        from .mpesa import refresh_giving_stk_status, stk_push_query, MpesaError
        if giving.status == 'pending':
            did, final_status = refresh_giving_stk_status(giving)
            giving.refresh_from_db()
            if did:
                messages.success(request, f'M-Pesa status updated: {giving.get_status_display()}.')
            else:
                # query once to surface reason/processing state if desired
                try:
                    res = stk_push_query(giving.mpesa_checkout_request_id)
                    code = res.get('result_code')
                    desc = res.get('result_desc') or res.get('response_description') or ''
                    if code is None and str(res.get('response_code')) == '0':
                        messages.info(request, f'M-Pesa payment is still processing. {desc}'.strip())
                    elif desc:
                        messages.info(request, f'M-Pesa status: {desc}')
                    else:
                        messages.info(request, 'No final M-Pesa result yet. Try again shortly.')
                except MpesaError as e:
                    messages.warning(request, f'Could not check M-Pesa status: {e}')
                except Exception:
                    messages.info(request, 'No final M-Pesa result yet. Try again shortly.')
        else:
            messages.info(request, f'M-Pesa status is already {giving.get_status_display()}.')
    except Exception as e:
        messages.error(request, f'Could not refresh M-Pesa status: {e}')
    return redirect('giving:giving-list')
