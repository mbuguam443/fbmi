"""
Clean up seeded/dummy data from production database.
ONLY removes records that are UNAMBIGUOUSLY fake (matching seed patterns).
Does NOT touch any real user data.

Run: python clean_seeded_data.py
"""
import os
import re
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_seeded_data.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    # File-based confirmation: if clean_confirm.txt exists with "YES", proceed
    confirm_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_confirm.txt')

    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Clean Seeded/Dummy Data ===')
            w(f, 'Mode: ' + ('DRY RUN (show only, no deletion)' if dry_run else 'DELETE MODE'))
            w(f, 'cwd: ' + os.getcwd())
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            if not dry_run and not os.path.exists(confirm_file):
                w(f, '\n*** SAFETY STOP ***')
                w(f, 'To actually delete, create a file named "clean_confirm.txt"')
                w(f, 'in the project root containing exactly: YES')
                w(f, 'Then run this script again.')
                w(f, '\nRun with --dry-run first to preview what would be deleted.')
                return

            if not dry_run:
                with open(confirm_file, 'r') as cf:
                    if cf.read().strip() != 'YES':
                        w(f, '\n*** CONFIRM FILE does not contain "YES" ***')
                        return

            from finance.models import Transaction
            from giving.models import Giving

            # ============ 1. Fake Transactions (from seed_data) ============
            w(f, '\n--- Fake Transactions (description: "Income record N" / "Expense record N") ---')
            fake_tx_income = Transaction.objects.filter(
                transaction_type='income',
                description__regex=r'^Income record \d+$'
            )
            fake_tx_expense = Transaction.objects.filter(
                transaction_type='expense',
                description__regex=r'^Expense record \d+$'
            )
            w(f, f'Fake income transactions: {fake_tx_income.count()} (total: {fake_tx_income.aggregate(sum=__import__("django").db.models.Sum("amount"))["sum"] or 0})')
            w(f, f'Fake expense transactions: {fake_tx_expense.count()} (total: {fake_tx_expense.aggregate(sum=__import__("django").db.models.Sum("amount"))["sum"] or 0})')
            for tx in fake_tx_income[:5]:
                w(f, f'  e.g. ID={tx.id} | {tx.description} | KSh {tx.amount} | {tx.date}')
            w(f, '  ...')

            # ============ 2. Fake Givings (from seed_data, REF##### refs) ============
            w(f, '\n--- Fake Givings (reference: "REF#####") ---')
            # Seed created givings with 5-digit REF numbers
            fake_givings = Giving.objects.filter(
                reference_number__regex=r'^REF\d{5}$'
            )
            w(f, f'Fake givings (REF##### pattern): {fake_givings.count()}')
            for g in fake_givings[:5]:
                member_name = f'{g.member.first_name} {g.member.last_name}' if g.member else 'No member'
                w(f, f'  e.g. ID={g.id} | {member_name} | KSh {g.amount} | ref={g.reference_number} | {g.date}')
            w(f, '  ...')

            # ============ 3. Auto-created Transactions from fake Givings ============
            w(f, '\n--- Auto-created Transactions linked to fake Givings ---')
            fake_giving_ids = list(fake_givings.values_list('id', flat=True))
            linked_tx = Transaction.objects.filter(
                giving_record__id__in=fake_giving_ids
            )
            w(f, f'Linked transactions from fake givings: {linked_tx.count()}')

            # ============ Summary before deletion ============
            total_fake_tx = fake_tx_income.count() + fake_tx_expense.count() + linked_tx.count()
            total_fake_givings = fake_givings.count()
            w(f, f'\n=== SUMMARY ===')
            w(f, f'Total fake transactions to delete: {total_fake_tx}')
            w(f, f'Total fake givings to delete: {total_fake_givings}')

            # Show what real data will remain
            real_tx = Transaction.objects.exclude(
                id__in=list(fake_tx_income.values_list('id', flat=True))
                + list(fake_tx_expense.values_list('id', flat=True))
                + list(linked_tx.values_list('id', flat=True))
            )
            real_givings = Giving.objects.exclude(
                id__in=fake_giving_ids
            )
            w(f, f'\n=== REAL DATA (WILL BE KEPT) ===')
            w(f, f'Real transactions remaining: {real_tx.count()}')
            w(f, f'Real givings remaining: {real_givings.count()}')
            for g in real_givings[:10]:
                member_name = f'{g.member.first_name} {g.member.last_name}' if g.member else 'Basket'
                w(f, f'  KEEP: ID={g.id} | {member_name} | KSh {g.amount} | {g.status} | ref={g.reference_number or "none"}')

            # ============ Deletion ============
            if not dry_run:
                w(f, '\n--- DELETING ---')
                # Delete linked transactions first (FK constraint)
                if linked_tx.exists():
                    deleted_linked = linked_tx.delete()
                    w(f, f'Deleted {deleted_linked[0]} linked transactions')

                # Delete fake givings (clear transaction FK first)
                if fake_givings.exists():
                    Giving.objects.filter(id__in=fake_giving_ids).update(transaction=None)
                    deleted_givings = fake_givings.delete()
                    w(f, f'Deleted {deleted_givings[0]} fake givings')

                # Delete fake transactions
                if fake_tx_income.exists():
                    deleted_income = fake_tx_income.delete()
                    w(f, f'Deleted {deleted_income[0]} fake income transactions')
                if fake_tx_expense.exists():
                    deleted_expense = fake_tx_expense.delete()
                    w(f, f'Deleted {deleted_expense[0]} fake expense transactions')

                # ============ After cleanup stats ============
                w(f, '\n=== AFTER CLEANUP ===')
                remaining_income = Transaction.objects.filter(transaction_type='income').aggregate(
                    sum=__import__('django').db.models.Sum('amount'))['sum'] or 0
                remaining_expense = Transaction.objects.filter(transaction_type='expense').aggregate(
                    sum=__import__('django').db.models.Sum('amount'))['sum'] or 0
                remaining_giving = Giving.objects.filter(status='completed').aggregate(
                    sum=__import__('django').db.models.Sum('amount'))['sum'] or 0
                w(f, f'Real total income: KSh {remaining_income}')
                w(f, f'Real total expenses: KSh {remaining_expense}')
                w(f, f'Real total giving: KSh {remaining_giving}')
                w(f, f'Real net balance: KSh {remaining_income - remaining_expense}')

                # Remove the confirmation file so it can't be accidentally re-run
                if os.path.exists(confirm_file):
                    os.remove(confirm_file)
                    w(f, '\nConfirmation file removed (safety).')
            else:
                w(f, '\n*** DRY RUN — no data was deleted ***')
                w(f, 'To delete for real:')
                w(f, '  1) Create clean_confirm.txt with "YES"')
                w(f, '  2) Run: python clean_seeded_data.py')

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
