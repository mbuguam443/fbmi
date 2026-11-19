"""Send Thursday fellowship reminder notification to all active members."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Send Thursday fellowship reminder (30 min before the 1 PM fellowship)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Send even if not Thursday or already sent today',
        )

    def handle(self, *args, **options):
        now = timezone.localtime()
        is_thursday = now.weekday() == 3  # Thursday = 3 (Mon=0)

        if not options.get('force'):
            if not is_thursday:
                self.stdout.write(f'Today is {now.strftime("%A")} — not Thursday. Skipping.')
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

        # Send the reminder (30 minutes before the 1 PM fellowship)
        from api.notify import broadcast
        User = get_user_model()
        count = User.objects.filter(is_active=True).count()

        broadcast(
            title='Thursday Fellowship in 30 Minutes',
            message='Reminder: Thursday fellowship starts at 1:00 PM (in 30 minutes). Please get ready and join us for a time of worship, word and fellowship. See you there!',
            kind='fellowship_reminder',
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Thursday fellowship reminder sent to {count} members at {now.strftime("%H:%M")}.'
            )
        )
