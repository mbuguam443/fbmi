from django.db import migrations


def add_prayer_perms(apps, schema_editor):
    RoleModulePermission = apps.get_model('core', 'RoleModulePermission')
    roles = RoleModulePermission.objects.values_list('role', flat=True).distinct()
    for role in roles:
        RoleModulePermission.objects.get_or_create(role=role, module='prayer')


def remove_prayer_perms(apps, schema_editor):
    RoleModulePermission = apps.get_model('core', 'RoleModulePermission')
    RoleModulePermission.objects.filter(module='prayer').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_notification_kind'),
    ]
    operations = [
        migrations.RunPython(add_prayer_perms, remove_prayer_perms),
    ]
