import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance_diag.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Attendance diagnosis ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())

            from django.conf import settings
            w(f, 'DEBUG: ' + str(settings.DEBUG))
            w(f, 'ALLOWED_HOSTS: ' + str(settings.ALLOWED_HOSTS))

            # dependency check
            for mod in ('qrcode', 'PIL'):
                try:
                    m = __import__(mod)
                    ver = getattr(m, '__version__', getattr(m, 'PILLOW_VERSION', 'ok'))
                    w(f, f'dep {mod}: OK {ver}')
                except Exception as e:
                    w(f, f'dep {mod}: MISSING/ERROR {e!r}')

            from services.models import Service
            from django.contrib.auth import get_user_model
            from django.test import Client

            services = list(Service.objects.order_by('-date')[:5])
            w(f, 'services(found): ' + str([(s.id, s.name, str(s.date)) for s in services]))
            if not services:
                w(f, 'No services found; nothing to test.')
                return

            U = get_user_model()
            u = U.objects.filter(is_superuser=True).first() or U.objects.first()
            w(f, 'user: ' + (str(u.username) if u else 'NONE'))

            settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver', 'localhost', '127.0.0.1']
            c = Client(raise_request_exception=False)
            if u:
                c.force_login(u)

            s = services[0]
            for path in [f'/attendance/service/{s.id}/', f'/attendance/service/{s.id}/qr/']:
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

            # also try direct QR generation
            w(f, '\n--- Direct QR generation ---')
            try:
                import base64, io
                from django.core import signing
                qr_token = signing.Signer(salt='attendance-qr').sign_object({'s': s.id})
                w(f, 'token ok len=' + str(len(qr_token)))
                import qrcode
                img = qrcode.make('fbmi://attend/' + qr_token)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                w(f, 'qr png bytes=' + str(len(buf.getvalue())))
            except Exception:
                w(f, traceback.format_exc())

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
