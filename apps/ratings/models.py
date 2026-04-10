"""
apps/ratings/models.py
Users can rate drivers from 1 to 5 stars after a trip.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import User
from apps.routes.models import Trip


class DriverRating(models.Model):
    driver     = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='ratings_received',
                     limit_choices_to={'role': 'driver'}
                 )
    rated_by   = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='ratings_given',
                     limit_choices_to={'role': 'user'}
                 )
    trip       = models.ForeignKey(
                     Trip, on_delete=models.SET_NULL,
                     null=True, blank=True,
                     related_name='ratings'
                 )
    stars      = models.PositiveSmallIntegerField(
                     validators=[MinValueValidator(1), MaxValueValidator(5)],
                     verbose_name='Note (1-5)'
                 )
    comment    = models.TextField(blank=True, verbose_name='Commentaire')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering            = ['-created_at']
        # One rating per user per trip
        unique_together     = ('rated_by', 'trip')

    def __str__(self):
        return f"{self.rated_by} → {self.driver} : {self.stars}⭐"