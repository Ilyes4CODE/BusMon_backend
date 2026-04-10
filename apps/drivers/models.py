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