from datetime import date
import base64
import io
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from communication.models import Announcement
from events.models import Event
from ministries.models import Ministry
from sermons.models import Sermon
from services.models import Service


def find_apk():
    for directory in getattr(settings, 'APK_DIRS', []):
        candidate = Path(directory) / getattr(settings, 'APK_FILENAME', 'fbmi-members.apk')
        if candidate.is_file():
            return candidate
    return None


def download_fbmi_apk(request):
    apk_path = find_apk()
    if apk_path is None:
        raise Http404('FBMI Members app is not available yet.')
    response = FileResponse(
        apk_path.open('rb'),
        as_attachment=True,
        filename=apk_path.name,
        content_type='application/vnd.android.package-archive',
    )
    response['Content-Length'] = apk_path.stat().st_size
    return response


class PublicAppDownloadView(TemplateView):
    template_name = 'public/app_download.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apk_path = find_apk()
        context['apk_available'] = apk_path is not None
        if apk_path:
            context['apk_size_mb'] = round(apk_path.stat().st_size / (1024 * 1024), 1)
        try:
            import qrcode
            download_url = self.request.build_absolute_uri(reverse('public:app_download'))
            image = qrcode.make(download_url)
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            context['app_qr'] = base64.b64encode(buffer.getvalue()).decode('ascii')
        except Exception:
            context['app_qr'] = None
        return context


class PublicHomeView(TemplateView):
    template_name = 'public/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()

        context['upcoming_events'] = Event.objects.filter(
            date__gte=today,
            is_active=True
        ).order_by('date', 'time')[:5]

        context['latest_sermons'] = Sermon.objects.all()[:5]
        context['ministries'] = Ministry.objects.filter(is_active=True)
        context['service_times'] = Service.objects.filter(
            date__gte=today
        ).order_by('date', 'start_time')[:3]
        context['announcements'] = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]

        return context


class PublicAboutView(TemplateView):
    template_name = 'public/about.html'


class PublicMinistriesView(ListView):
    model = Ministry
    template_name = 'public/ministries.html'
    context_object_name = 'ministries'

    def get_queryset(self):
        return Ministry.objects.filter(is_active=True)


class PublicServicesView(ListView):
    model = Service
    template_name = 'public/services.html'
    context_object_name = 'services'

    def get_queryset(self):
        return Service.objects.filter(
            date__gte=date.today()
        ).order_by('date', 'start_time')


class PublicEventsView(ListView):
    model = Event
    template_name = 'public/events.html'
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.filter(
            date__gte=date.today(),
            is_active=True
        ).order_by('date', 'time')


class PublicSermonsView(ListView):
    model = Sermon
    template_name = 'public/sermons.html'
    context_object_name = 'sermons'
    paginate_by = 10


class PublicContactView(TemplateView):
    template_name = 'public/contact.html'


class PublicGiveView(TemplateView):
    template_name = 'public/give.html'
