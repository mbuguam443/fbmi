import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrate_out.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Run migrations ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            from django.core.management import call_command
            from io import StringIO

            out = StringIO()
            err = StringIO()
            try:
                call_command('migrate', '--noinput', verbosity=1, stdout=out, stderr=err)
                w(f, '\n--- stdout ---')
                w(f, out.getvalue() or '(empty)')
                w(f, '\n--- stderr ---')
                w(f, err.getvalue() or '(empty)')
                w(f, '\nSTATUS: OK')
            except SystemExit as e:
                w(f, '\n--- stdout ---')
                w(f, out.getvalue() or '(empty)')
                w(f, '\n--- stderr ---')
                w(f, err.getvalue() or '(empty)')
                w(f, '\nSystemExit: ' + str(e))
                w(f, traceback.format_exc())
            except Exception:
                w(f, '\n--- stdout ---')
                w(f, out.getvalue() or '(empty)')
                w(f, '\n--- stderr ---')
                w(f, err.getvalue() or '(empty)')
                w(f, '\nEXCEPTION:')
                w(f, traceback.format_exc())

            # show unapplied migrations if any
            w(f, '\n--- showmigrations (unapplied marked [ ]) ---')
            out2 = StringIO()
            try:
                call_command('showmigrations', '--plan', stdout=out2, stderr=StringIO())
                # keep output manageable
                text = out2.getvalue()
                lines = text.splitlines()
                # include all; file is fine
                for line in lines:
                    w(f, line)
            except Exception:
                w(f, traceback.format_exc())

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
