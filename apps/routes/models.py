"""
routes/models.py  +  drivers/models.py
Combined here for clarity — split into separate files in actual project.
"""

# ════════════════════════════════════════
# FILE: apps/routes/models.py
# ════════════════════════════════════════

from django.db import models
from apps.buses.models import Bus
from apps.accounts.models import User


class Route(models.Model):
    name        = models.CharField(max_length=200, verbose_name='Nom du trajet')
    origin      = models.CharField(max_length=200, verbose_name='Point de départ')
    destination = models.CharField(max_length=200, verbose_name='Point d\'arrivée')
    distance_km = models.FloatField(null=True, blank=True, verbose_name='Distance (km)')
    duration_min= models.PositiveIntegerField(null=True, blank=True, verbose_name='Durée estimée (min)')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Trajet'
        verbose_name_plural = 'Trajets'
        ordering            = ['name']

    def __str__(self):
        return f"{self.name} ({self.origin} → {self.destination})"


class Stop(models.Model):
    route  = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    name   = models.CharField(max_length=200)
    order  = models.PositiveIntegerField()
    lat    = models.FloatField(null=True, blank=True)
    lng    = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.route.name} - Arrêt {self.order}: {self.name}"


class Trip(models.Model):
    """A scheduled trip = Route + Bus + Driver + time."""

    class Status(models.TextChoices):
        SCHEDULED  = 'scheduled',  'Planifiée'
        IN_PROGRESS= 'in_progress','En cours'
        COMPLETED  = 'completed',  'Terminée'
        CANCELLED  = 'cancelled',  'Annulée'
        DELAYED    = 'delayed',    'Retardée'

    route       = models.ForeignKey(Route, on_delete=models.PROTECT, related_name='trips')
    bus         = models.ForeignKey(Bus, on_delete=models.PROTECT, related_name='trips',
                                    null=True, blank=True)
    driver      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='trips', limit_choices_to={'role': 'driver'})
    departure_time = models.DateTimeField(verbose_name='Heure de départ')
    arrival_time   = models.DateTimeField(null=True, blank=True, verbose_name='Heure d\'arrivée')
    status      = models.CharField(max_length=15, choices=Status.choices,
                                   default=Status.SCHEDULED)
    delay_minutes  = models.IntegerField(default=0, verbose_name='Retard (min)')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Rotation'
        verbose_name_plural = 'Rotations'
        ordering            = ['-departure_time']

    def __str__(self):
        return f"{self.route.name} - {self.departure_time:%d/%m/%Y %H:%M}"