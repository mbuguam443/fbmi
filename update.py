#!/usr/bin/env python
"""
FBMI Church - Update Script
Run this after uploading changes to cPanel to apply updates.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')

import django
django.setup()

from django.core.management import call_command

print("=" * 50)
print("FBMI Church - Running Update")
print("=" * 50)

print("\n1. Running migrations...")
call_command('migrate')
print("   Migrations completed!")

print("\n2. Collecting static files...")
call_command('collectstatic', '--noinput')
print("   Static files collected!")

restart = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp', 'restart.txt')
os.makedirs(os.path.dirname(restart), exist_ok=True)
with open(restart, 'w') as f:
    f.write('')
print("\n3. Passenger restart triggered.")

print("\n" + "=" * 50)
print("UPDATE COMPLETED SUCCESSFULLY!")
print("=" * 50)
