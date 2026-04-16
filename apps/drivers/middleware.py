"""Create daily absence-history rows on first request of each calendar day (no cron required)."""

from django.core.cache import cache
from django.utils import timezone


class DailyAbsenceHistoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._ensure_daily_records()
        return self.get_response(request)

    def _ensure_daily_records(self):
        from apps.accounts.models import User

        from .models import AbsenceHistory

        today = timezone.localdate()
        key = f'absence_daily_roll_{today.isoformat()}'
        if cache.get(key):
            return

        driver_ids = list(
            User.objects.filter(
                role=User.Role.DRIVER,
                driver_profile__isnull=False,
            ).values_list('id', flat=True)
        )
        if not driver_ids:
            cache.set(key, 1, timeout=86400)
            return

        existing = set(
            AbsenceHistory.objects.filter(date=today, driver_id__in=driver_ids).values_list(
                'driver_id', flat=True
            )
        )
        missing = [uid for uid in driver_ids if uid not in existing]
        if missing:
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
        cache.set(key, 1, timeout=86400)
