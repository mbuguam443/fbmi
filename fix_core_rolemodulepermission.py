import os
import sys
import traceback
from io import StringIO

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_core_rolemodulepermission.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Fix core_rolemodulepermission ===')
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings')
            import django
            django.setup()
            from django.db import connection
            from django.core.management import call_command

            tables = connection.introspection.table_names()
            w(f, 'has core_rolemodulepermission: ' + str('core_rolemodulepermission' in tables))
            w(f, 'has core_churchsettings: ' + str('core_churchsettings' in tables))

            if 'core_rolemodulepermission' in tables:
                w(f, 'Table already exists. Nothing to do.')
                w(f, '\n=== DONE ===')
                return

            # Table missing but migrations are likely recorded as applied. Reset core to 0003 (fake)
            # then migrate forward to create 0004+ properly.
            w(f, 'Table missing. Running: migrate core 0003 --fake')
            buf = StringIO()
            try:
                call_command('migrate', 'core', '0003', fake=True, stdout=buf, stderr=buf, verbosity=1)
            except Exception:
                w(f, buf.getvalue())
                raise
            w(f, buf.getvalue() or '(no output)')

            w(f, 'Running: migrate core')
            buf = StringIO()
            try:
                call_command('migrate', 'core', stdout=buf, stderr=buf, verbosity=1)
            except Exception:
                w(f, buf.getvalue())
                raise
            w(f, buf.getvalue() or '(no output)')

            tables = connection.introspection.table_names()
            w(f, 'has core_rolemodulepermission now: ' + str('core_rolemodulepermission' in tables))
            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
