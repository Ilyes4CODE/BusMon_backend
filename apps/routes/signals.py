"""Trip lifecycle → driver availability (not tied to a fixed bus)."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.drivers.models import DriverProfile

from .models import Trip


def _trip_driver_ids(trip: Trip):
    ids = []
    if trip.driver_id:
        ids.append(trip.driver_id)
    if trip.second_driver_id:
        ids.append(trip.second_driver_id)
    return ids


@receiver(post_save, sender=Trip)
def sync_driver_availability_on_trip(sender, instance: Trip, **kwargs):
    ids = _trip_driver_ids(instance)
    if not ids:
        return
    if instance.status in (Trip.Status.COMPLETED, Trip.Status.CANCELLED):
        DriverProfile.objects.filter(user_id__in=ids).update(is_available=True)
    elif instance.status == Trip.Status.IN_PROGRESS:
        DriverProfile.objects.filter(user_id__in=ids).update(is_available=False)
