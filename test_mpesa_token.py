"""Standalone test: try multiple methods to reach Safaricom Daraja and get an access token."""
import base64
import os
import sys
import traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_mpesa_token.txt')

KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
PASSKEY = os.environ.get('MPESA_PASSKEY', '')
ENV = os.environ.get('MPESA_ENV', 'sandbox')
CALLBACK = os.environ.get('MPESA_CALLBACK_URL', '')

BASE_SANDBOX = 'https://sandbox.safaricom.co.ke'
BASE_PROD = 'https://api.safaricom.co.ke'
BASE = BASE_PROD if ENV == 'production' else BASE_SANDBOX
TOKEN_URL = BASE + '/oauth/v1/generate?grant_type=client_credentials'


def w(f, msg=''):
    f.write(str(msg) + '\n')
    f.flush()


def main():
    with open(OUT, 'w', encoding='utf-8') as f:
        try:
            w(f, '=== M-Pesa token access test ===')
            w(f, 'cwd: ' + os.getcwd())
            w(f, 'python: ' + sys.version)
            w(f, 'env: ' + ENV)
            w(f, 'base: ' + BASE)

            # Load .env if python-dotenv is available
            try:
                from dotenv import load_dotenv
                from pathlib import Path
                env_file = Path(__file__).resolve().parent / '.env'
                if env_file.exists():
                    load_dotenv(env_file, override=True)
                    w(f, '.env loaded from: ' + str(env_file))
                    # re-read after loading
                    globals()['KEY'] = os.environ.get('MPESA_CONSUMER_KEY', '')
                    globals()['SECRET'] = os.environ.get('MPESA_CONSUMER_SECRET', '')
                    globals()['SHORTCODE'] = os.environ.get('MPESA_SHORTCODE', '')
                    globals()['PASSKEY'] = os.environ.get('MPESA_PASSKEY', '')
                    globals()['ENV'] = os.environ.get('MPESA_ENV', 'sandbox')
                    globals()['BASE'] = BASE_PROD if ENV == 'production' else BASE_SANDBOX
                    globals()['TOKEN_URL'] = BASE + '/oauth/v1/generate?grant_type=client_credentials'
            except ImportError:
                w(f, 'python-dotenv not available; using env vars only')

            w(f, 'key present: ' + ('YES' if KEY else 'NO'))
            w(f, 'secret present: ' + ('YES' if SECRET else 'NO'))
            w(f, '')

            import requests

            # Method 1: Default requests
            w(f, '--- Method 1: default requests ---')
            try:
                r = requests.get(TOKEN_URL, auth=(KEY, SECRET), timeout=15)
                w(f, f'status: {r.status_code}')
                w(f, f'content-type: {r.headers.get("content-type","?")}')
                if r.status_code == 200:
                    data = r.json()
                    token = data.get('access_token', '')
                    w(f, 'TOKEN: ' + (token[:8] + '...' if token else 'NONE'))
                else:
                    w(f, f'body[:200]: {r.text[:200]}')
            except Exception as e:
                w(f, f'ERROR: {e}')
            w(f, '')

            # Method 2: Browser-like User-Agent
            w(f, '--- Method 2: browser User-Agent ---')
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                }
                r = requests.get(TOKEN_URL, auth=(KEY, SECRET), headers=headers, timeout=15)
                w(f, f'status: {r.status_code}')
                if r.status_code == 200:
                    data = r.json()
                    token = data.get('access_token', '')
                    w(f, 'TOKEN: ' + (token[:8] + '...' if token else 'NONE'))
                else:
                    w(f, f'body[:200]: {r.text[:200]}')
            except Exception as e:
                w(f, f'ERROR: {e}')
            w(f, '')

            # Method 3: urllib (no requests library)
            w(f, '--- Method 3: urllib ---')
            try:
                import urllib.request
                import urllib.error
                import json as json_mod
                # Build basic auth header manually
                creds = base64.b64encode(f'{KEY}:{SECRET}'.encode()).decode()
                req = urllib.request.Request(TOKEN_URL)
                req.add_header('Authorization', f'Basic {creds}')
                req.add_header('User-Agent', 'Mozilla/5.0')
                with urllib.request.urlopen(req, timeout=15) as resp:
                    w(f, f'status: {resp.status}')
                    data = json_mod.loads(resp.read().decode())
                    token = data.get('access_token', '')
                    w(f, 'TOKEN: ' + (token[:8] + '...' if token else 'NONE'))
            except urllib.error.HTTPError as e:
                w(f, f'HTTP ERROR: {e.code}')
                w(f, f'body[:200]: {e.read().decode("utf-8","ignore")[:200]}')
            except Exception as e:
                w(f, f'ERROR: {e}')
            w(f, '')

            # Method 4: curl subprocess (if available)
            w(f, '--- Method 4: curl ---')
            try:
                import subprocess
                cmd = [
                    'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                    '-u', f'{KEY}:{SECRET}',
                    TOKEN_URL,
                    '--max-time', '15',
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                w(f, f'status: {result.stdout.strip()}')
                if result.stdout.strip() == '200':
                    # get the body
                    cmd2 = ['curl', '-s', '-u', f'{KEY}:{SECRET}', TOKEN_URL, '--max-time', '15']
                    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=20)
                    data = json_mod.loads(r2.stdout) if r2.stdout else {}
                    token = data.get('access_token', '')
                    w(f, 'TOKEN: ' + (token[:8] + '...' if token else 'NONE'))
                else:
                    w(f, 'curl failed or not available')
            except FileNotFoundError:
                w(f, 'curl not found on server')
            except Exception as e:
                w(f, f'ERROR: {e}')
            w(f, '')

            # Method 5: DNS resolution check
            w(f, '--- DNS check ---')
            try:
                import socket
                if ENV == 'production':
                    host = 'api.safaricom.co.ke'
                else:
                    host = 'sandbox.safaricom.co.ke'
                w(f, f'resolving {host}...')
                ip = socket.gethostbyname(host)
                w(f, f'IP: {ip}')
            except Exception as e:
                w(f, f'DNS ERROR: {e}')
            w(f, '')

            # Method 6: Raw TCP connection test
            w(f, '--- TCP connection test (port 443) ---')
            try:
                import socket
                host = 'sandbox.safaricom.co.ke' if ENV != 'production' else 'api.safaricom.co.ke'
                sock = socket.create_connection((host, 443), timeout=10)
                w(f, f'TCP connect to {host}:443 OK')
                sock.close()
            except Exception as e:
                w(f, f'TCP ERROR: {e}')
            w(f, '')

            w(f, '=== DONE ===')
        except Exception:
            w(f, 'FATAL:')
            w(f, traceback.format_exc())


if __name__ == '__main__':
    main()
    print('Wrote ' + OUT)
