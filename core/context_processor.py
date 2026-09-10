from .models import ChurchSetting


def church_settings(request):
    try:
        settings = ChurchSetting.get_settings()
    except Exception:
        settings = None
    return {
        'church_settings': settings,
    }
