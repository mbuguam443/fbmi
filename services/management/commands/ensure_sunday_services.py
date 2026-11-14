from django.core.management.base import BaseCommand

from services.utils import ensure_upcoming_sunday_services


class Command(BaseCommand):
    help = "Ensure upcoming Sunday services exist so they are ready for attendance, QR, and setlists."

    def add_arguments(self, parser):
        parser.add_argument("--weeks", type=int, default=4, help="How many upcoming Sundays to ensure. Default: 4.")
        parser.add_argument("--name", default="Sunday Service", help='Service name to create. Default: "Sunday Service".')
        parser.add_argument("--start-time", default="10:00", help="Start time in HH:MM (24h). Default: 10:00.")
        parser.add_argument("--location", default="", help="Default location (optional).")

    def handle(self, *args, **options):
        created = ensure_upcoming_sunday_services(
            weeks=options["weeks"],
            name=options["name"],
            start_time=options["start-time"],
            location=options.get("location") or "",
        )
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} service(s), ensured {options['weeks']} upcoming Sunday(s)."))

