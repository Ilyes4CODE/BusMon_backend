from django.db import models
from apps.accounts.models import User


class Notification(models.Model):

    class NotifType(models.TextChoices):
        DELAY       = 'delay',       'Retard'
        BREAKDOWN   = 'breakdown',   'Panne'
        SCHEDULE    = 'schedule',    'Changement horaire'
        MAINTENANCE = 'maintenance', 'Maintenance'
        GENERAL     = 'general',     'Général'

    recipient  = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='notifications', null=True, blank=True)
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    type       = models.CharField(max_length=15, choices=NotifType.choices,
                                  default=NotifType.GENERAL)
    is_read    = models.BooleanField(default=False)
    data       = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering            = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.title}"