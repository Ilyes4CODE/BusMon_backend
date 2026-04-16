"""Run daily (e.g. cron at 00:05): python manage.py create_daily_absence_history"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.drivers.models import AbsenceHistory


class Command(BaseCommand):
    help = 'Creates absence-history rows for today for every driver (idempotent).'

    def handle(self, *args, **options):
        today = timezone.localdate()
        driver_ids = list(
            User.objects.filter(
                role=User.Role.DRIVER,
                driver_profile__isnull=False,
            ).values_list('id', flat=True)
        )
        existing = set(
            AbsenceHistory.objects.filter(date=today, driver_id__in=driver_ids).values_list(
                'driver_id', flat=True
            )
        )
        missing = [uid for uid in driver_ids if uid not in existing]
        if not missing:
            self.stdout.write(self.style.SUCCESS(f'All drivers already have a row for {today}.'))
            return
        AbsenceHistory.objects.bulk_create(
            [
                AbsenceHistory(
                    driver_id=uid,
                    date=today,
                    status=AbsenceHistory.DayStatus.PRESENT,
                    auto_generated=True,
                )
                for uid in missing
            ]
        )
        self.stdout.write(self.style.SUCCESS(f'Created {len(missing)} absence-history row(s) for {today}.'))
