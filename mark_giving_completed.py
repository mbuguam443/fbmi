import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mark_giving_completed_out.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    # File-based usage (recommended for cPanel/file-run):
    #   1) Edit mark_giving_ids.txt and put IDs to mark completed (e.g. 78 79 80 81, or one per line)
    #   2) Run this script: python mark_giving_completed.py
    # CLI usage also supported: python mark_giving_completed.py 78 79 [--ref TESTREF] [--note "reason"]
    args = sys.argv[1:]
    ids = []
    ref = None
    note = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--id', '-i') and i + 1 < len(args):
            try:
                ids.append(int(args[i + 1]))
            except Exception:
                pass
            i += 2
            continue
        if a in ('--ref', '-r') and i + 1 < len(args):
            ref = args[i + 1]
            i += 2
            continue
        if a in ('--note', '-n') and i + 1 < len(args):
            note = args[i + 1]
            i += 2
            continue
        if a.isdigit():
            ids.append(int(a))
        i += 1

    if not ids:
        ids_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mark_giving_ids.txt')
        if os.path.exists(ids_file):
            try:
                with open(ids_file, 'r', encoding='utf-8') as idf:
                    text = idf.read()
                # allow spaces, commas, newlines
                for part in text.replace(',', ' ').replace('\n', ' ').split():
                    part = part.strip()
                    if part.isdigit():
                        ids.append(int(part))
            except Exception:
                pass

    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Mark giving(s) completed (TEST/ADMIN) ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            from giving.models import Giving

            if not ids:
                w(f, 'No giving IDs provided.')
                w(f, 'Usage: python mark_giving_completed.py 78 79 [--ref TESTREF] [--note "reason"]')
                return

            for gid in ids:
                g = Giving.objects.filter(id=gid).first()
                if not g:
                    w(f, f'id={gid}: NOT FOUND')
                    continue
                before = g.status
                g.status = 'completed'
                if ref:
                    g.reference_number = ref
                elif not g.reference_number:
                    g.reference_number = f'TEST-{g.id}'
                extra = note or 'Manually marked completed (test)'
                g.notes = (g.notes or '') + f' | {extra}'.strip(' |')
                g.save(update_fields=['status', 'reference_number', 'notes', 'updated_at'])
                w(f, f'id={g.id}: {before} -> {g.status} amount={g.amount} ref={g.reference_number}')
                w(f, f'  notes={g.notes}')

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
