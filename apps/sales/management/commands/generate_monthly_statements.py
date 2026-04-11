import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Monthly statements: created={created}, skipped={skipped}, month={month}, year={year}"
            )
        )
