"""
maintenance/models.py
"""

from django.db import models
from apps.buses.models import Bus
from apps.accounts.models import User


class MaintenanceRecord(models.Model):

    class MaintenanceType(models.TextChoices):
        PREVENTIVE = 'preventive', 'Préventive'
        CORRECTIVE = 'corrective', 'Corrective'
        INSPECTION = 'inspection', 'Inspection'

    bus         = models.ForeignKey(Bus, on_delete=models.CASCADE,
                                    related_name='maintenance_records')
    type        = models.CharField(max_length=15, choices=MaintenanceType.choices)
    description = models.TextField(verbose_name='Description des travaux')
    cost        = models.DecimalField(max_digits=10, decimal_places=2,
                                      null=True, blank=True, verbose_name='Coût (DZD)')
    performed_by= models.CharField(max_length=200, blank=True, verbose_name='Réalisé par')
    date        = models.DateField(verbose_name='Date de maintenance')
    next_date   = models.DateField(null=True, blank=True, verbose_name='Prochaine maintenance')
    mileage     = models.PositiveIntegerField(null=True, blank=True, verbose_name='Kilométrage')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, related_name='maintenance_records')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Maintenance'
        verbose_name_plural = 'Maintenances'
        ordering            = ['-date']

    def __str__(self):
        return f"{self.bus.plate_number} - {self.type} - {self.date}"


class Breakdown(models.Model):

    class BreakdownStatus(models.TextChoices):
        REPORTED    = 'reported',    'Signalée'
        IN_PROGRESS = 'in_progress', 'En cours de résolution'
        RESOLVED    = 'resolved',    'Résolue'

    bus          = models.ForeignKey(Bus, on_delete=models.CASCADE,
                                     related_name='breakdowns')
    reported_by  = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, related_name='reported_breakdowns')
    description  = models.TextField(verbose_name='Description de la panne')
    location_desc= models.CharField(max_length=300, blank=True,
                                    verbose_name='Lieu de la panne')
    latitude     = models.FloatField(null=True, blank=True)
    longitude    = models.FloatField(null=True, blank=True)
    status       = models.CharField(max_length=15, choices=BreakdownStatus.choices,
                                    default=BreakdownStatus.REPORTED)

    # Driver Alert — driver presses alert button in app
    alert_sent    = models.BooleanField(default=False, verbose_name='Alerte envoyée')
    alert_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Heure d'alerte")
    alert_message = models.TextField(blank=True, verbose_name="Message d'alerte du chauffeur")

    # Resolution — driver must fill root_cause before bus returns to work
    root_cause       = models.TextField(blank=True, verbose_name='Cause principale de la panne')
    resolution_notes = models.TextField(blank=True, verbose_name='Actions effectuées')
    resolved_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='resolved_breakdowns')
    reported_at  = models.DateTimeField(auto_now_add=True)
    resolved_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Panne'
        verbose_name_plural = 'Pannes'
        ordering            = ['-reported_at']

    def __str__(self):
        return f"Panne - {self.bus.plate_number} - {self.reported_at:%d/%m/%Y}"