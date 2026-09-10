#!/usr/bin/env python
"""
FBMI Church - Update Script
Run this after uploading changes to cPanel to apply updates.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fbms.settings_production')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

print("\n" + "=" * 50)
print("UPDATE COMPLETED SUCCESSFULLY!")
print("=" * 50)
print("\nRestart your app from cPanel to apply changes.")
