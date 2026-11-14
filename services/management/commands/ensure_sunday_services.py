from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand

from services.models import Service


class Command(BaseCommand):
    help = "Ensure upcoming Sunday services exist so they are ready for attendance, QR, and setlists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=4,
            help="How many upcoming Sundays to ensure (including this coming Sunday). Default: 4.",
        )
        parser.add_argument(
            "--name",
            default="Sunday Service",
            help='Service name to create. Default: "Sunday Service".',
        )
        parser.add_argument(
            "--start-time",
            default="10:00",
            help="Start time in HH:MM (24h). Default: 10:00.",
        )
        parser.add_argument(
            "--location",
            default="",
            help="Default location (optional).",
        )

    def handle(self, *args, **options):
        weeks = max(1, int(options["weeks"]))
        name = options["name"]
        location = options.get("location") or ""
        try:
            start_time = datetime.strptime(options["start_time"], "%H:%M").time()
        except ValueError:
            self.stderr.write(self.style.ERROR("Invalid --start-time, expected HH:MM (e.g. 10:00)."))
            return

        today = date.today()
        # Next Sunday (0=Mon..6=Sun). If today is Sunday, include today.
        days_ahead = (6 - today.weekday()) % 7
        first = today + timedelta(days=days_ahead)

        created = 0
        for i in range(weeks):
            d = first + timedelta(weeks=i)
            obj, was_created = Service.objects.get_or_create(
                date=d,
                name=name,
                defaults={
                    "start_time": start_time,
                    "location": location,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name} on {obj.date} {obj.start_time}"))
            else:
                self.stdout.write(f"Exists:  {obj.name} on {obj.date}")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} service(s), ensured {weeks} upcoming Sunday(s)."))
