"""File-based wrapper: send Thursday fellowship reminder (for cPanel cron).
Same as running `python manage.py send_fellowship_reminder` but works
without shell arguments — just run this file.

Usage (cPanel cron):
  /home/wlsihszp/virtualenv/fbmi/3.11/bin/python /home/wlsihszp/fbmi/run_fellowship_reminder.py

Cron schedule: 30 12 * * 4  (Thursday at 12:30 PM)
"""
import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fellowship_reminder_log.txt')


def main():
    with open(OUT, 'a', encoding='utf-8') as f:
        try:
            f.write(f'\n=== {os.environ.get("DJANGO_SETTINGS_MODULE", "fbms.settings_production")} run at {__import__("datetime").datetime.now().isoformat()} ===\n')
            f.flush()

            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

            import django
            django.setup()

            from django.core.management import call_command
            from io import StringIO

            out = StringIO()
            err = StringIO()
            call_command('send_fellowship_reminder', stdout=out, stderr=err)

            f.write(out.getvalue() + '\n')
            if err.getvalue():
                f.write('STDERR:\n' + err.getvalue() + '\n')
            f.write('=== DONE ===\n')
            f.flush()

            # Also print to stdout for cron logs
            print(out.getvalue())
        except Exception:
            f.write('FATAL:\n')
            f.write(traceback.format_exc())
            f.write('=== FAILED ===\n')
            f.flush()
            print(traceback.format_exc())


if __name__ == '__main__':
    main()
