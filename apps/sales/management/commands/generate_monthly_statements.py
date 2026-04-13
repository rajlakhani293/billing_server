import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.settings.models import Party
from apps.sales.service import SalesService


class Command(BaseCommand):
    help = "Generate monthly statements and opening balance entries for parties"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, default=None, help="Year (YYYY)")
        parser.add_argument("--month", type=int, default=None, help="Month (1-12)")
        parser.add_argument(
            "--all",
            action="store_true",
            help="Generate for all parties even if opening balance is 0",
        )

    def handle(self, *args, **options):
        # Log startup information similar to Django development server
        self.stdout.write(self.style.SUCCESS("System check identified no issues (0 silenced)."))
        
        now = timezone.localtime()
        self.stdout.write(f"{now.strftime('%B %d, %Y - %H:%M:%S')}")
        
        import django
        self.stdout.write(f"Django version {django.get_version()}, using settings '{settings.SETTINGS_MODULE}'")
        self.stdout.write(self.style.SUCCESS("Starting monthly statement generation..."))
        self.stdout.write("")

        today = timezone.localdate()
        year = options.get("year") or today.year
        month = options.get("month") or today.month
        include_all = bool(options.get("all"))

        created = 0
        skipped = 0

        parties = Party.objects.filter(status__in=[0, 1])

        for party in parties.iterator():
            statement = SalesService.generateMonthlyStatementForParty(party, year, month, allow_zero=include_all)
            if statement:
                created += 1
            else:
                skipped += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Monthly statements generation completed successfully: created={created}, skipped={skipped}, month={month}, year={year}"
            )
        )
        self.stdout.write(self.style.SUCCESS("Cron job execution finished."))
