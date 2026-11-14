import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagnose_service_detail.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Service detail diagnosis ===')
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings')
            import django
            django.setup()
            from django.conf import settings
            from django.test import Client
            from django.contrib.auth import get_user_model
            from services.models import Service

            w(f, 'DEBUG: ' + str(settings.DEBUG))
            services = list(Service.objects.order_by('-date').values('id', 'name', 'date')[:10])
            w(f, 'services: ' + str(services))

            U = get_user_model()
            u = U.objects.filter(is_superuser=True).first() or U.objects.first()
            w(f, 'user: ' + (str(u.username) if u else 'NONE'))

            settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver', 'localhost', '127.0.0.1']
            c = Client(raise_request_exception=False)
            if u:
                c.force_login(u)

            # test service 7 explicitly and latest
            ids = []
            if Service.objects.filter(pk=7).exists():
                ids.append(7)
            first = Service.objects.order_by('-date').first()
            if first and first.id not in ids:
                ids.append(first.id)
            if not ids and services:
                ids.append(services[0]['id'])

            for sid in ids:
                for path in [f'/services/{sid}/', f'/attendance/service/{sid}/', f'/attendance/service/{sid}/qr/']:
                    w(f, '\n--- TEST ' + path + ' ---')
                    try:
                        r = c.get(path, HTTP_HOST='localhost')
                        w(f, 'status: ' + str(r.status_code))
                        content = r.content.decode('utf-8', 'ignore')
                        if r.status_code >= 500:
                            idx = content.find('Traceback')
                            if idx != -1:
                                w(f, content[idx:idx + 8000])
                            else:
                                w(f, content[:4000])
                        else:
                            w(f, 'ok (len=' + str(len(content)) + ')')
                    except Exception:
                        w(f, 'EXCEPTION:')
                        w(f, traceback.format_exc())

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
