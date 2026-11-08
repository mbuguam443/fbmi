from django.core.management.base import BaseCommand

from api.notify import broadcast


class Command(BaseCommand):
    help = 'Send a test in-app + push notification to every active member.'

    def add_arguments(self, parser):
        parser.add_argument('--title', default='Test notification')
        parser.add_argument('--message', default='Real-time notifications are working.')
        parser.add_argument('--kind', default='announcements')

    def handle(self, *args, **options):
        broadcast(options['title'], options['message'], options['kind'], '/notifications')
        self.stdout.write(self.style.SUCCESS('Test notification sent to all active members.'))
