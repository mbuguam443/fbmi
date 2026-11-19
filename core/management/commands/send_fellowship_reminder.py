"""Send Thursday fellowship reminder notification to all active members."""
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Send Thursday fellowship reminder to all active members (1 PM reminder)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Send even if not Thursday or already sent today',
        )

    def handle(self, *args, **options):
        now = timezone.localtime()
        is_thursday = now.weekday() == 3  # Thursday = 3 (Mon=0)
        is_past_1pm = now.hour >= 13

        if not options.get('force'):
            if not is_thursday:
                self.stdout.write(f'Today is {now.strftime("%A")} — not Thursday. Skipping.')
                self.stdout.write('Use --force to send anyway.')
                return
            if not is_past_1pm:
                self.stdout.write(f'It is {now.strftime("%H:%M")} — before 1 PM. Skipping.')
                self.stdout.write('Use --force to send anyway.')
                return

        # Check if already sent today
        from core.models import Notification
        already_sent = Notification.objects.filter(
            kind='fellowship_reminder',
            created_at__date=now.date(),
        ).exists()

        if already_sent and not options.get('force'):
            self.stdout.write('Thursday fellowship reminder already sent today. Skipping.')
            return

        # Send the reminder
        from api.notify import broadcast
        User = get_user_model()
        count = User.objects.filter(is_active=True).count()

        broadcast(
            title='Thursday Fellowship Today',
            message='Reminder: Thursday fellowship is today at 1:00 PM. Please be ready and join us for a time of worship, word and fellowship. See you there!',
            kind='fellowship_reminder',
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Thursday fellowship reminder sent to {count} members at {now.strftime("%H:%M")}.'
            )
        )
