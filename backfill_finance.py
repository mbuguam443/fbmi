"""Backfill: create finance Transaction records from existing completed Giving records."""
import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backfill_finance.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== Backfill finance from giving ===')
            w(f, 'cwd: ' + os.getcwd())
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            from giving.models import Giving
            from finance.models import Transaction

            # Find completed givings without a linked transaction
            completed = Giving.objects.filter(status='completed', transaction__isnull=True)
            w(f, f'Completed givings without transaction: {completed.count()}')

            created = 0
            skipped = 0
            for g in completed:
                try:
                    cat = g.giving_category if g.giving_category in dict(Transaction.INCOME_CATEGORIES) else 'other'
                    member_part = f' from {g.member.first_name} {g.member.last_name}' if g.member else ' (Basket)'
                    tx = Transaction.objects.create(
                        transaction_type='income',
                        amount=g.amount,
                        category=cat,
                        description=f'Giving: {g.get_giving_category_display()} via {g.get_payment_method_display()}{member_part}',
                        date=g.date,
                        member=g.member,
                    )
                    g.transaction = tx
                    g.save(update_fields=['transaction'])
                    created += 1
                    w(f, f'  + Giving #{g.id} ({g.amount} KES {g.giving_category}) -> Transaction #{tx.id}')
                except Exception as e:
                    skipped += 1
                    w(f, f'  ! Giving #{g.id} skipped: {e}')

            w(f, f'\nCreated: {created} | Skipped: {skipped}')

            # Show summary
            w(f, '\n--- Finance summary after backfill ---')
            income = Transaction.objects.filter(transaction_type='income').aggregate(total=__import__('django').db.models.Sum('amount'))['total'] or 0
            expense = Transaction.objects.filter(transaction_type='expense').aggregate(total=__import__('django').db.models.Sum('amount'))['total'] or 0
            w(f, f'Total income: {income} KES')
            w(f, f'Total expense: {expense} KES')
            w(f, f'Net balance: {income - expense} KES')
            w(f, f'Total transactions: {Transaction.objects.count()}')

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
