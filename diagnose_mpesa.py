import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpesa_diag.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def mask(val):
    s = str(val or '')
    if not s:
        return '<EMPTY>'
    if len(s) <= 8:
        return s[:2] + '***'
    return s[:4] + '...' + s[-4:] + f' (len={len(s)})'


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== M-Pesa diagnosis ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            from django.conf import settings
            w(f, 'DEBUG: ' + str(settings.DEBUG))

            keys = [
                'MPESA_CONSUMER_KEY',
                'MPESA_CONSUMER_SECRET',
                'MPESA_SHORTCODE',
                'MPESA_PASSKEY',
                'MPESA_ENV',
                'MPESA_CALLBACK_URL',
            ]
            w(f, '\n--- settings (masked) ---')
            for k in keys:
                v = getattr(settings, k, None)
                if k in ('MPESA_ENV', 'MPESA_SHORTCODE', 'MPESA_CALLBACK_URL'):
                    w(f, f'{k}: {v!r}')
                else:
                    w(f, f'{k}: {mask(v)}')

            w(f, '\n--- env vars present (masked) ---')
            for k in keys:
                v = os.getenv(k)
                if k in ('MPESA_ENV', 'MPESA_SHORTCODE', 'MPESA_CALLBACK_URL'):
                    w(f, f'{k}: {v!r}')
                else:
                    w(f, f'{k}: {mask(v)}')

            w(f, '\n--- dependency/import ---')
            try:
                import requests
                w(f, 'requests: OK ' + getattr(requests, '__version__', '?'))
            except Exception as e:
                w(f, 'requests: MISSING/ERROR ' + repr(e))

            try:
                from giving.mpesa import normalize_phone, get_access_token, MpesaError
                w(f, 'giving.mpesa: OK')
                w(f, 'normalize_phone(0712345678): ' + normalize_phone('0712345678'))
            except Exception:
                w(f, 'giving.mpesa import: ERROR')
                w(f, traceback.format_exc())
                return

            w(f, '\n--- access token test ---')
            try:
                token = get_access_token()
                w(f, 'access_token: OK ' + mask(token))
            except MpesaError as e:
                w(f, 'MpesaError: ' + str(e))
            except Exception:
                w(f, 'Exception:')
                w(f, traceback.format_exc())

            w(f, '\n--- recent M-Pesa givings ---')
            try:
                from giving.models import Giving
                qs = Giving.objects.filter(payment_method='mpesa').order_by('-id')[:10]
                for g in qs:
                    w(f, f'id={g.id} status={getattr(g,"status","?")} amount={g.amount} phone={getattr(g,"phone_number","")} ref={g.reference_number} date={getattr(g,"date","")} created={getattr(g,"created_at","")} checkout={getattr(g,"mpesa_checkout_request_id","")} merchant={getattr(g,"mpesa_merchant_request_id","")}')
                    w(f, f'  notes={getattr(g,"notes","")}')
            except Exception:
                w(f, traceback.format_exc())

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
