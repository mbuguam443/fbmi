from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, TemplateView,
)

from .models import Transaction


class FinanceAccessMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_finance

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access finance records.')
        return super().handle_no_permission()


class FinanceDashboardView(LoginRequiredMixin, FinanceAccessMixin, TemplateView):
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = Transaction.objects.all()
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # This month's stats
        monthly = transactions.filter(date__gte=month_start.date())
        income = monthly.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        expense = monthly.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        context['total_income'] = income
        context['total_expense'] = expense
        context['net_balance'] = income - expense
        context['transaction_count'] = monthly.count()

        # All-time stats
        all_income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        all_expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        context['all_time_income'] = all_income
        context['all_time_expense'] = all_expense
        context['all_time_balance'] = all_income - all_expense

        context['recent_transactions'] = transactions.select_related('member', 'recorded_by')[:10]

        # Income by category (with percentages)
        income_items = list(
            transactions.filter(transaction_type='income')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        income_total = sum(i['total'] for i in income_items) or 1
        for item in income_items:
            item['percentage'] = round((item['total'] / income_total) * 100, 1)
            item['category_label'] = dict(Transaction.INCOME_CATEGORIES).get(item['category'], item['category'].title())
        context['income_by_category'] = income_items

        # Expenses by category (with percentages)
        expense_items = list(
            transactions.filter(transaction_type='expense')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        expense_total = sum(e['total'] for e in expense_items) or 1
        for item in expense_items:
            item['percentage'] = round((item['total'] / expense_total) * 100, 1)
            item['category_label'] = dict(Transaction.EXPENSE_CATEGORIES).get(item['category'], item['category'].title())
        context['expense_by_category'] = expense_items

        # Monthly summary (last 6 months)
        from datetime import date
        monthly_data = []
        for i in range(5, -1, -1):
            m_start = (now.replace(day=1) - __import__('datetime').timedelta(days=32 * i)).replace(day=1)
            m_end = (m_start + __import__('datetime').timedelta(days=32)).replace(day=1)
            m_income = transactions.filter(
                transaction_type='income', date__gte=m_start.date(), date__lt=m_end.date()
            ).aggregate(total=Sum('amount'))['total'] or 0
            m_expense = transactions.filter(
                transaction_type='expense', date__gte=m_start.date(), date__lt=m_end.date()
            ).aggregate(total=Sum('amount'))['total'] or 0
            monthly_data.append({
                'month': m_start.strftime('%B %Y'),
                'short': m_start.strftime('%b'),
                'income': m_income,
                'expense': m_expense,
                'net': m_income - m_expense,
            })
        context['monthly_summary'] = monthly_data

        return context


class TransactionListView(LoginRequiredMixin, FinanceAccessMixin, ListView):
    model = Transaction
    template_name = 'finance/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        transaction_type = self.request.GET.get('type', '').strip()
        category = self.request.GET.get('category', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        search = self.request.GET.get('search', '').strip()

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if category:
            queryset = queryset.filter(category=category)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_filter'] = self.request.GET.get('type', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['search'] = self.request.GET.get('search', '')
        context['type_choices'] = Transaction.TYPE_CHOICES
        context['income_categories'] = Transaction.INCOME_CATEGORIES
        context['expense_categories'] = Transaction.EXPENSE_CATEGORIES

        # Analytics for this page
        all_tx = Transaction.objects.all()
        context['total_income'] = all_tx.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        context['total_expense'] = all_tx.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        context['net_balance'] = context['total_income'] - context['total_expense']
        context['transaction_count'] = all_tx.count()

        # Filtered total for footer
        filtered_income = self.object_list.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        filtered_expense = self.object_list.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        context['filtered_income'] = filtered_income
        context['filtered_expense'] = filtered_expense
        context['filtered_net'] = filtered_income - filtered_expense

        return context


import csv


def export_transactions_csv(request):
    """Export filtered transactions as CSV."""
    if not request.user.is_authenticated or not request.user.is_finance:
        return redirect('accounts:login')

    transactions = Transaction.objects.select_related('member', 'recorded_by').order_by('-date', '-created_at')

    # Apply same filters as the list view
    transaction_type = request.GET.get('type', '').strip()
    category = request.GET.get('category', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search = request.GET.get('search', '').strip()

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if category:
        transactions = transactions.filter(category=category)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search)
            | Q(category__icontains=search)
            | Q(member__first_name__icontains=search)
            | Q(member__last_name__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="fbmi_transactions_{timezone.localdate().isoformat()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Type', 'Category', 'Description', 'Member', 'Recorded By', 'Amount (KSh)'])
    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.created_at.strftime('%H:%M') if t.created_at else '',
            t.get_transaction_type_display(),
            dict(Transaction.INCOME_CATEGORIES).get(t.category, dict(Transaction.EXPENSE_CATEGORIES).get(t.category, t.category.title())) if t.transaction_type == 'income' else dict(Transaction.EXPENSE_CATEGORIES).get(t.category, t.category.title()),
            t.description,
            f'{t.member.first_name} {t.member.last_name}' if t.member else '',
            f'{t.recorded_by.first_name} {t.recorded_by.last_name}' if t.recorded_by else '',
            str(t.amount),
        ])
    return response


class TransactionCreateView(LoginRequiredMixin, FinanceAccessMixin, CreateView):
    model = Transaction
    template_name = 'finance/transaction_form.html'
    fields = ['transaction_type', 'amount', 'category', 'description', 'date', 'member']
    success_url = reverse_lazy('finance:transaction-list')

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Transaction recorded successfully.')
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, FinanceAccessMixin, UpdateView):
    model = Transaction
    template_name = 'finance/transaction_form.html'
    fields = ['transaction_type', 'amount', 'category', 'description', 'date', 'member']
    success_url = reverse_lazy('finance:transaction-list')

    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully.')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, FinanceAccessMixin, DeleteView):
    model = Transaction
    template_name = 'finance/transaction_confirm_delete.html'
    context_object_name = 'transaction'
    success_url = reverse_lazy('finance:transaction-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Transaction deleted successfully.')
        return super().delete(request, *args, **kwargs)
