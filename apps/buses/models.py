from django.db import models


class Bus(models.Model):

    class Status(models.TextChoices):
        MOVING      = 'moving',      'En mouvement'
        STOPPED     = 'stopped',     'À l\'arrêt'
        MAINTENANCE = 'maintenance', 'En maintenance'
        INACTIVE    = 'inactive',    'Inactif'

    plate_number  = models.CharField(max_length=20, unique=True)
    model         = models.CharField(max_length=100)
    brand         = models.CharField(max_length=100)
    capacity      = models.PositiveIntegerField(default=40)
    year          = models.PositiveIntegerField()
    status        = models.CharField(max_length=15, choices=Status.choices, default=Status.INACTIVE)

    # Real-time GPS
    latitude      = models.FloatField(null=True, blank=True)
    longitude     = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    is_active  = models.BooleanField(default=True)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Bus'
        verbose_name_plural = 'Bus'
        ordering            = ['plate_number']

    def __str__(self):
        return f"{self.brand} {self.model} - {self.plate_number}"