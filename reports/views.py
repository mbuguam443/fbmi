from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from members.models import Member
from attendance.models import Attendance
from giving.models import Giving
from finance.models import Transaction
from visitors.models import Visitor
from services.models import Service
from prayer.models import PrayerRequest


class ReportsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Quick stats (real data)
        context['total_members'] = Member.objects.filter(membership_status='active').count()
        context['total_visitors'] = Visitor.objects.count()
        context['visitors_this_year'] = Visitor.objects.filter(visit_date__gte=year_start.date()).count()
        context['total_giving'] = Giving.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        context['monthly_giving'] = Giving.objects.filter(
            status='completed', date__gte=month_start.date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['total_transactions'] = Transaction.objects.count()
        context['total_income'] = Transaction.objects.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        context['total_expenses'] = Transaction.objects.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        context['net_balance'] = context['total_income'] - context['total_expenses']

        # Active this month (members who attended at least once this month)
        context['active_this_month'] = Attendance.objects.filter(
            service__date__gte=month_start.date()
        ).values('member').distinct().count()

        # Attendance this month
        context['attendance_this_month'] = Attendance.objects.filter(
            service__date__gte=month_start.date()
        ).count()

        # Pending prayer requests
        context['pending_prayers'] = PrayerRequest.objects.exclude(status__in=['answered', 'completed']).count()

        # Recent activity (real data from database)
        activities = []

        # Recent services with attendance
        recent_services = Service.objects.filter(date__lte=now.date()).order_by('-date')[:3]
        for svc in recent_services:
            count = Attendance.objects.filter(service=svc).count()
            activities.append({
                'icon': 'bi-calendar2-check',
                'color': 'text-success',
                'title': svc.name,
                'date': svc.date,
                'detail': f'{count} attended',
            })

        # Recent new members
        recent_members = Member.objects.order_by('-created_at')[:3] if hasattr(Member, 'created_at') else Member.objects.order_by('-id')[:3]
        for m in recent_members:
            activities.append({
                'icon': 'bi-person-plus',
                'color': 'text-primary',
                'title': f'{m.first_name} {m.last_name} joined',
                'date': getattr(m, 'created_at', getattr(m, 'date_joined', now)),
                'detail': f'Membership: {m.get_membership_status_display() if hasattr(m, "get_membership_status_display") else m.membership_status}',
            })

        # Recent givings
        recent_givings = Giving.objects.filter(status='completed').order_by('-created_at')[:3]
        for g in recent_givings:
            name = f'{g.member.first_name} {g.member.last_name}' if g.member else 'Basket Offering'
            activities.append({
                'icon': 'bi-gift',
                'color': 'text-warning',
                'title': f'{name} gave KSh {g.amount}',
                'date': g.created_at,
                'detail': f'{g.get_giving_category_display()} via {g.get_payment_method_display()}',
            })

        # Recent prayer requests
        recent_prayers = PrayerRequest.objects.order_by('-created_at')[:2]
        for p in recent_prayers:
            activities.append({
                'icon': 'bi-heart',
                'color': 'text-danger',
                'title': f'Prayer: {p.title}',
                'date': p.created_at,
                'detail': f'Status: {p.get_status_display()}',
            })

        # Sort by date (convert everything to timestamp for safe comparison), take top 6
        def sort_key(a):
            d = a['date']
            if d is None:
                return now.timestamp()
            try:
                if hasattr(d, 'timestamp'):
                    return d.timestamp()
                # date object: convert to timestamp
                import datetime as dt
                return dt.datetime.combine(d, dt.time.min).timestamp()
            except Exception:
                return 0

        activities.sort(key=sort_key, reverse=True)
        context['recent_activities'] = activities[:6]

        # Giving trend (last 6 months)
        trend = []
        for i in range(5, -1, -1):
            m_start = (now.replace(day=1) - timedelta(days=32 * i)).replace(day=1)
            m_end = (m_start + timedelta(days=32)).replace(day=1)
            total = Giving.objects.filter(
                status='completed', date__gte=m_start.date(), date__lt=m_end.date()
            ).aggregate(total=Sum('amount'))['total'] or 0
            trend.append({
                'month': m_start.strftime('%b'),
                'total': total,
            })
        context['giving_trend'] = trend

        return context


class MembershipReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/membership_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = Member.objects.all()

        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        if start_date:
            members = members.filter(date_joined__gte=start_date)
        if end_date:
            members = members.filter(date_joined__lte=end_date)

        context['members'] = members
        context['total'] = members.count()
        context['by_status'] = members.values('membership_status').annotate(count=Count('id')).order_by('membership_status')
        context['by_gender'] = members.values('gender').annotate(count=Count('id')).order_by('gender')
        context['by_type'] = members.values('membership_type').annotate(count=Count('id')).order_by('membership_type')
        context['by_marital_status'] = members.values('marital_status').annotate(count=Count('id')).order_by('marital_status')
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context


class AttendanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/attendance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attendances = Attendance.objects.all()

        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        if start_date:
            attendances = attendances.filter(service__date__gte=start_date)
        if end_date:
            attendances = attendances.filter(service__date__lte=end_date)

        context['attendances'] = attendances
        context['total_records'] = attendances.count()
        context['by_type'] = attendances.values('attendance_type').annotate(count=Count('id')).order_by('attendance_type')
        context['by_service'] = attendances.values('service__name').annotate(count=Count('id')).order_by('-count')[:20]
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context


class GivingReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/giving_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        givings = Giving.objects.all()

        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        if start_date:
            givings = givings.filter(date__gte=start_date)
        if end_date:
            givings = givings.filter(date__lte=end_date)

        context['givings'] = givings.select_related('member')
        context['total_amount'] = givings.aggregate(total=Sum('amount'))['total'] or 0
        context['total_records'] = givings.count()
        context['completed_count'] = givings.filter(status='completed').count()
        context['average_amount'] = givings.aggregate(avg=Avg('amount'))['avg'] or 0
        context['by_category'] = givings.values('giving_category').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')
        context['by_payment_method'] = givings.values('payment_method').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context


class FinanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/finance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = Transaction.objects.all()

        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0

        context['transactions'] = transactions.select_related('member')
        context['total_income'] = income
        context['total_expenses'] = expense
        context['net_balance'] = income - expense
        context['transaction_count'] = transactions.count()
        income_items = list(transactions.filter(transaction_type='income').values('category').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total'))
        for item in income_items:
            item['category_label'] = dict(Transaction.INCOME_CATEGORIES).get(item['category'], item['category'].title())
        context['income_by_category'] = income_items
        expense_items = list(transactions.filter(transaction_type='expense').values('category').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total'))
        for item in expense_items:
            item['category_label'] = dict(Transaction.EXPENSE_CATEGORIES).get(item['category'], item['category'].title())
        context['expense_by_category'] = expense_items
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context


class VisitorReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/visitor_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visitors = Visitor.objects.all()

        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        if start_date:
            visitors = visitors.filter(visit_date__gte=start_date)
        if end_date:
            visitors = visitors.filter(visit_date__lte=end_date)

        context['visitors'] = visitors
        context['total'] = visitors.count()
        context['joined_count'] = visitors.filter(follow_up_status='joined').count()
        context['by_status'] = visitors.values('follow_up_status').annotate(count=Count('id')).order_by('follow_up_status')
        context['by_how_heard'] = visitors.values('how_they_heard').annotate(count=Count('id')).order_by('-count')
        context['by_service'] = visitors.values('service_attended').annotate(count=Count('id')).order_by('-count')
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context
