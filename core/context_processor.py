from .models import ChurchSetting, RoleModulePermission


def church_settings(request):
    try:
        settings = ChurchSetting.get_settings()
    except Exception:
        settings = None
    return {
        'church_settings': settings,
    }


def module_permissions(request):
    allowed = None
    if request.user.is_authenticated:
        allowed = RoleModulePermission.allowed_modules_for(request.user.role)
    return {
        'allowed_modules': allowed,
    }