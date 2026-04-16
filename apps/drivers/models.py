"""
drivers/models.py
"""

from django.db import models
from apps.accounts.models import User


class DriverProfile(models.Model):
    """Extended profile for drivers."""
    user            = models.OneToOneField(User, on_delete=models.CASCADE,
                                           related_name='driver_profile',
                                           limit_choices_to={'role': 'driver'})
    license_number  = models.CharField(max_length=50, unique=True, verbose_name='N° Permis')
    license_expiry  = models.DateField(verbose_name='Expiration permis')
    experience_years= models.PositiveIntegerField(default=0, verbose_name='Années d\'expérience')
    is_available    = models.BooleanField(default=True, verbose_name='Disponible')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Profil chauffeur'
        verbose_name_plural = 'Profils chauffeurs'

    def __str__(self):
        return f"Chauffeur: {self.user.get_full_name()}"


class Absence(models.Model):

    class AbsenceType(models.TextChoices):
        SICK      = 'sick',      'Maladie'
        VACATION  = 'vacation',  'Congé'
        UNJUSTIFIED='unjustified','Non justifiée'
        OTHER     = 'other',     'Autre'

    driver     = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='absences',
                                   limit_choices_to={'role': 'driver'})
    start_date = models.DateField(verbose_name='Date début')
    end_date   = models.DateField(verbose_name='Date fin')
    type       = models.CharField(max_length=15, choices=AbsenceType.choices,
                                  default=AbsenceType.OTHER)
    reason     = models.TextField(blank=True, verbose_name='Motif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Absence'
        verbose_name_plural = 'Absences'
        ordering            = ['-start_date']

    def __str__(self):
        return f"{self.driver.get_full_name()} absent du {self.start_date} au {self.end_date}"


class AbsenceHistory(models.Model):
    """One row per driver per calendar day (attendance / absence snapshot)."""

    class DayStatus(models.TextChoices):
        PRESENT = 'present', 'Présent'
        ABSENT  = 'absent',  'Absent'
        LEAVE   = 'leave',   'Congé'
        SICK    = 'sick',    'Maladie'

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='absence_history',
        limit_choices_to={'role': 'driver'},
    )
    date = models.DateField(verbose_name='Jour')
    status = models.CharField(
        max_length=10,
        choices=DayStatus.choices,
        default=DayStatus.PRESENT,
    )
    notes = models.TextField(blank=True)
    auto_generated = models.BooleanField(default=False, verbose_name='Créé automatiquement')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historique absence (journalier)'
        verbose_name_plural = 'Historique absences (journalier)'
        ordering = ['-date', 'driver__last_name']
        constraints = [
            models.UniqueConstraint(fields=['driver', 'date'], name='uniq_driver_absence_day'),
        ]

    def __str__(self):
        return f"{self.driver.get_full_name()} — {self.date} ({self.get_status_display()})"