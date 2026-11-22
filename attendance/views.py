import base64
import io

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ModelForm
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, DeleteView, DetailView, TemplateView
from accounts.views import ContentWriteMixin
from .models import Attendance
from .qr import make_service_token, make_sunday_token, resolve_sunday_service
from services.models import Service

try:
    import qrcode
except ImportError:  # pragma: no cover
    qrcode = None


def _qr_image_b64(qr_url):
    """Render a print-quality QR PNG as a base64 data URI payload."""
    if qrcode is None:
        return '', 'QR library not available on server. Install qrcode and Pillow.'
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,   # larger modules for crisp printing
            border=4,      # quiet zone (per QR spec)
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode('ascii'), ''
    except Exception as exc:
        return '', str(exc)


class AttendanceForm(ModelForm):
    class Meta:
        model = Attendance
        fields = ['service', 'member', 'attendance_type', 'visitor_name', 'notes']


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        service_id = self.request.GET.get('service', '')
        date = self.request.GET.get('date', '')

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if date:
            queryset = queryset.filter(service__date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.all()
        context['service_filter'] = self.request.GET.get('service', '')
        context['date_filter'] = self.request.GET.get('date', '')
        return context


class AttendanceCreateView(LoginRequiredMixin, ContentWriteMixin, CreateView):
    model = Attendance
    template_name = 'attendance/attendance_form.html'
    fields = ['service', 'member', 'attendance_type', 'visitor_name', 'notes']
    success_url = reverse_lazy('attendance:attendance_list')

    def form_valid(self, form):
        messages.success(self.request, 'Attendance record created successfully.')
        return super().form_valid(form)


class AttendanceByServiceView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'attendance/attendance_by_service.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object.attendances.select_related('member').all()
        context['attendances'] = qs
        context['attendance_records'] = qs
        context['total_count'] = qs.count()
        context['member_count'] = qs.filter(attendance_type='member').count()
        context['visitor_count'] = qs.filter(attendance_type='visitor').count()
        context['online_count'] = qs.filter(attendance_type='online').count()
        context['attendance_form'] = AttendanceForm(initial={'service': self.object})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, 'Attendee added successfully.')
            return redirect('attendance:by_service', pk=self.object.pk)
        context = self.get_context_data(object=self.object)
        context['attendance_form'] = form
        return self.render_to_response(context)


class AttendanceDeleteView(LoginRequiredMixin, ContentWriteMixin, DeleteView):
    model = Attendance
    template_name = 'attendance/attendance_confirm_delete.html'
    success_url = reverse_lazy('attendance:attendance_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Attendance record deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ServiceQRView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'attendance/service_qr.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        qr_token = make_service_token(service.id)
        qr_url = 'fbmi://attend/%s' % qr_token
        qr_b64, qr_error = _qr_image_b64(qr_url)
        context['qr_error'] = qr_error
        context['qr_token'] = qr_token
        context['qr_url'] = qr_url
        context['qr_b64'] = qr_b64
        return context


class SundayQRView(LoginRequiredMixin, TemplateView):
    """One permanent QR code for every Sunday service."""
    template_name = 'attendance/sunday_qr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qr_token = make_sunday_token()
        qr_url = 'fbmi://attend/%s' % qr_token
        qr_b64, qr_error = _qr_image_b64(qr_url)
        context['qr_error'] = qr_error
        context['qr_token'] = qr_token
        context['qr_url'] = qr_url
        context['qr_b64'] = qr_b64
        context['is_sunday'] = timezone.localdate().weekday() == 6
        context['current_service'] = resolve_sunday_service() if context['is_sunday'] else None
        return context
