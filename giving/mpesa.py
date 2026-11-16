import base64
import datetime
import json
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings


class MpesaError(Exception):
    pass


def _base_url():
    env = (getattr(settings, 'MPESA_ENV', 'sandbox') or 'sandbox').lower()
    if env == 'production':
        return 'https://api.safaricom.co.ke'
    return 'https://sandbox.safaricom.co.ke'


def normalize_phone(phone):
    """Normalize Kenyan phone numbers to 2547XXXXXXXX / 2541XXXXXXXX format."""
    if not phone:
        return ''
    p = ''.join(ch for ch in str(phone) if ch.isdigit() or ch == '+')
    p = p.lstrip('+')
    if p.startswith('0') and len(p) == 10:
        p = '254' + p[1:]
    elif p.startswith('7') and len(p) == 9:
        p = '254' + p
    elif p.startswith('1') and len(p) == 9:
        p = '254' + p
    return p


def get_access_token():
    key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
    secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
    if not key or not secret:
        raise MpesaError('M-Pesa consumer key/secret not configured.')
    url = _base_url() + '/oauth/v1/generate?grant_type=client_credentials'
    try:
        resp = requests.get(url, auth=(key, secret), timeout=30)
    except requests.exceptions.RequestException as e:
        raise MpesaError(f'Could not reach M-Pesa to get access token: {e}')
    try:
        data = resp.json()
    except Exception:
        body = (resp.text or '').strip().replace('\n', ' ')[:200]
        raise MpesaError(f'Failed to get access token (HTTP {resp.status_code}){": " + body if body else ""}')
    token = data.get('access_token')
    if not token:
        err = data.get('errorMessage') or data.get('error_description') or data.get('fault', {}).get('faultstring') if isinstance(data.get('fault'), dict) else None
        raise MpesaError(err or f'Failed to get access token (HTTP {resp.status_code}).')
    return token


def stk_push(phone, amount, account_reference='FBMI Giving', transaction_desc='Church giving', callback_url=None):
    shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
    passkey = getattr(settings, 'MPESA_PASSKEY', '')
    if not shortcode or not passkey:
        raise MpesaError('M-Pesa shortcode/passkey not configured.')

    phone = normalize_phone(phone)
    if not (phone.startswith('254') and len(phone) == 12):
        raise MpesaError('Enter a valid phone number (e.g. 07XXXXXXXX or 2547XXXXXXXX).')

    try:
        amt = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        raise MpesaError('Enter a valid amount.')
    if amt <= 0:
        raise MpesaError('Amount must be greater than zero.')
    # STK push expects whole shillings in most cases
    amt_int = int(amt.quantize(Decimal('1')))
    if amt_int <= 0:
        raise MpesaError('Amount must be at least 1.')

    callback_url = callback_url or getattr(settings, 'MPESA_CALLBACK_URL', '')
    if not callback_url:
        raise MpesaError('M-Pesa callback URL not configured (MPESA_CALLBACK_URL).')

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()
    token = get_access_token()

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amt_int,
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': callback_url,
        'AccountReference': (account_reference or 'FBMI Giving')[:12],
        'TransactionDesc': (transaction_desc or 'Church giving')[:13],
    }
    url = _base_url() + '/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.exceptions.RequestException as e:
        raise MpesaError(f'Could not reach M-Pesa to send STK push: {e}')
    try:
        data = resp.json()
    except Exception:
        raise MpesaError(f'STK push failed (HTTP {resp.status_code}).')

    if str(data.get('ResponseCode')) == '0':
        return {
            'ok': True,
            'merchant_request_id': data.get('MerchantRequestID', ''),
            'checkout_request_id': data.get('CheckoutRequestID', ''),
            'response_description': data.get('ResponseDescription') or data.get('CustomerMessage') or 'STK push sent.',
            'customer_message': data.get('CustomerMessage') or '',
        }
    raise MpesaError(data.get('errorMessage') or data.get('ResponseDescription') or data.get('CustomerMessage') or 'STK push failed.')


def stk_push_query(checkout_request_id):
    """Query Daraja for STK push transaction status."""
    shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
    passkey = getattr(settings, 'MPESA_PASSKEY', '')
    if not shortcode or not passkey:
        raise MpesaError('M-Pesa shortcode/passkey not configured.')
    checkout_request_id = (checkout_request_id or '').strip()
    if not checkout_request_id:
        raise MpesaError('Missing CheckoutRequestID.')

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()
    token = get_access_token()

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    url = _base_url() + '/mpesa/stkpushquery/v1/query'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.exceptions.RequestException as e:
        raise MpesaError(f'Could not reach M-Pesa to query STK status: {e}')

    try:
        data = resp.json()
    except Exception:
        body = (resp.text or '').strip().replace('\n', ' ')[:200]
        raise MpesaError(f'STK query failed (HTTP {resp.status_code}){": " + body if body else ""}')

    # Daraja returns ResponseCode/ResultCode/ResultDesc in various forms
    result_code = data.get('ResultCode')
    if result_code is None:
        # sometimes under ResponseCode for the query request itself
        resp_code = data.get('ResponseCode')
        if resp_code is not None and str(resp_code) != '0':
            raise MpesaError(data.get('errorMessage') or data.get('ResponseDescription') or data.get('errorCode') or f'STK query failed: {data}')
    result_desc = data.get('ResultDesc') or data.get('ResponseDescription') or ''
    return {
        'ok': True,
        'raw': data,
        'result_code': result_code,
        'result_desc': result_desc,
        'merchant_request_id': data.get('MerchantRequestID', ''),
        'checkout_request_id': data.get('CheckoutRequestID', checkout_request_id),
        'response_code': data.get('ResponseCode'),
        'response_description': data.get('ResponseDescription', ''),
    }


def apply_stk_query_result(giving, query_result):
    """Apply STK query result to a Giving record and persist changes. Returns (updated, final_status)."""
    code = query_result.get('result_code')
    code_str = str(code) if code is not None else ''
    desc = query_result.get('result_desc') or query_result.get('response_description') or ''

    if code_str == '0':
        if giving.status != 'completed':
            giving.status = 'completed'
            giving.notes = (giving.notes or '') + f' | Query: success - {desc}'.strip(' |')
            giving.save(update_fields=['status', 'notes', 'updated_at'])
            return True, 'completed'
        return False, giving.status

    if code_str in ('1032', '1037', '1', '2001', '9999'):
        # 1032 cancelled, 1037 timeout/cannot reach, others common failure codes
        if giving.status not in ('completed', 'failed', 'cancelled'):
            giving.status = 'failed'
            giving.notes = (giving.notes or '') + f' | Query: failed/cancelled ({code_str}) - {desc}'.strip(' |')
            giving.save(update_fields=['status', 'notes', 'updated_at'])
            return True, 'failed'
        return False, giving.status

    # request accepted but no final result yet, or unknown code
    if code is None and str(query_result.get('response_code')) == '0':
        # still processing; don't spam notes on every poll
        return False, giving.status

    return False, giving.status


def refresh_giving_stk_status(giving):
    """Query Daraja for a pending M-Pesa STK giving and update it if a final result is available."""
    if not giving or getattr(giving, 'payment_method', '') != 'mpesa':
        return False, getattr(giving, 'status', None)
    if getattr(giving, 'status', '') != 'pending':
        return False, giving.status
    checkout_id = (getattr(giving, 'mpesa_checkout_request_id', '') or '').strip()
    if not checkout_id:
        return False, giving.status
    try:
        res = stk_push_query(checkout_id)
    except MpesaError:
        return False, giving.status
    except Exception:
        return False, giving.status
    return apply_stk_query_result(giving, res)


def refresh_pending_stk_givings(givings):
    """Refresh pending STK statuses for an iterable/queryset of givings. Returns number updated."""
    updated = 0
    for g in givings:
        try:
            did, _ = refresh_giving_stk_status(g)
            if did:
                updated += 1
        except Exception:
            continue
    return updated


def parse_stk_callback(body):
    """Parse Safaricom STK callback payload into a simple dict."""
    try:
        stk = body.get('Body', {}).get('stkCallback', {})
    except Exception:
        stk = {}
    result_code = stk.get('ResultCode')
    result = {
        'merchant_request_id': stk.get('MerchantRequestID', ''),
        'checkout_request_id': stk.get('CheckoutRequestID', ''),
        'result_code': result_code,
        'result_desc': stk.get('ResultDesc', ''),
        'success': str(result_code) == '0',
        'amount': None,
        'receipt_number': '',
        'phone_number': '',
        'transaction_date': None,
    }
    if result['success']:
        items = stk.get('CallbackMetadata', {}).get('Item', []) or []
        meta = {item.get('Name'): item.get('Value') for item in items if isinstance(item, dict)}
        result['amount'] = meta.get('Amount')
        result['receipt_number'] = str(meta.get('MpesaReceiptNumber') or '')
        result['phone_number'] = str(meta.get('PhoneNumber') or '')
        result['transaction_date'] = meta.get('TransactionDate')
    return result
