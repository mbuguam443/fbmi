import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpesa_stk_query.txt')


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    giving_id = None
    checkout_id = None
    args = sys.argv[1:]
    # usage: python query_mpesa_stk.py --id 78  OR  --checkout ws_CO_xxx
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--id', '-i') and i + 1 < len(args):
            try:
                giving_id = int(args[i + 1])
            except Exception:
                giving_id = None
            i += 2
            continue
        if a in ('--checkout', '-c') and i + 1 < len(args):
            checkout_id = args[i + 1].strip()
            i += 2
            continue
        if a.isdigit() and giving_id is None and checkout_id is None:
            giving_id = int(a)
        i += 1

    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== M-Pesa STK Query ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
            import django
            django.setup()
            w(f, 'django: ' + django.get_version())
            w(f, 'settings: ' + os.environ.get('DJANGO_SETTINGS_MODULE', ''))

            from giving.models import Giving
            from giving.mpesa import stk_push_query, MpesaError

            giving = None
            if giving_id is not None:
                giving = Giving.objects.filter(id=giving_id).first()
                if not giving:
                    w(f, f'Giving id={giving_id} not found.')
                    return
            elif checkout_id:
                giving = Giving.objects.filter(mpesa_checkout_request_id=checkout_id).first()
                if not giving:
                    w(f, f'Giving with checkout {checkout_id!r} not found in DB; will still query Daraja.')
            else:
                # default: latest pending mpesa with checkout id
                giving = Giving.objects.filter(payment_method='mpesa', status='pending').exclude(mpesa_checkout_request_id='').order_by('-id').first()
                if not giving:
                    w(f, 'No pending M-Pesa giving with checkout_request_id found. Pass --id <giving_id> or --checkout <CheckoutRequestID>.')
                    return

            if giving:
                checkout_id = checkout_id or getattr(giving, 'mpesa_checkout_request_id', '')
                w(f, f'Giving: id={giving.id} status={giving.status} amount={giving.amount} phone={getattr(giving,"phone_number","")} ref={giving.reference_number}')
                w(f, f'  checkout={getattr(giving,"mpesa_checkout_request_id","")} merchant={getattr(giving,"mpesa_merchant_request_id","")}')
                w(f, f'  notes={getattr(giving,"notes","")}')

            w(f, f'\nQuerying CheckoutRequestID: {checkout_id}')
            try:
                res = stk_push_query(checkout_id)
            except MpesaError as e:
                w(f, 'MpesaError: ' + str(e))
                return
            except Exception:
                w(f, 'Exception:')
                w(f, traceback.format_exc())
                return

            w(f, '\n--- query result ---')
            w(f, 'result_code: ' + str(res.get('result_code')))
            w(f, 'result_desc: ' + str(res.get('result_desc')))
            w(f, 'response_code: ' + str(res.get('response_code')))
            w(f, 'response_description: ' + str(res.get('response_description')))
            w(f, 'raw: ' + str(res.get('raw')))

            # interpret and update giving if present
            if giving:
                code = res.get('result_code')
                code_str = str(code) if code is not None else ''
                desc = res.get('result_desc') or res.get('response_description') or ''
                if code_str == '0':
                    giving.status = 'completed'
                    giving.notes = (giving.notes or '') + f' | Query: success - {desc}'.strip(' |')
                    giving.save(update_fields=['status', 'notes', 'updated_at'])
                    w(f, '\nUPDATED giving: status=completed')
                elif code_str in ('1032', '1037', '1', '2001'):
                    # 1032 cancelled by user, 1037 timeout/unreachable, others failure
                    giving.status = 'failed'
                    giving.notes = (giving.notes or '') + f' | Query: failed/cancelled ({code_str}) - {desc}'.strip(' |')
                    giving.save(update_fields=['status', 'notes', 'updated_at'])
                    w(f, f'\nUPDATED giving: status=failed ({code_str})')
                elif code is None and str(res.get('response_code')) == '0':
                    # request accepted but no final result yet
                    giving.notes = (giving.notes or '') + f' | Query: still processing - {desc}'.strip(' |')
                    giving.save(update_fields=['notes', 'updated_at'])
                    w(f, '\nNOT UPDATED (still processing); notes appended')
                else:
                    giving.notes = (giving.notes or '') + f' | Query: result={code_str} - {desc}'.strip(' |')
                    giving.save(update_fields=['notes', 'updated_at'])
                    w(f, f'\nNOT UPDATED (code={code_str}); notes appended')

            w(f, '\n=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
