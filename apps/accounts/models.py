from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN  = 'admin',  'Administrateur'
        DRIVER = 'driver', 'Chauffeur'
        USER   = 'user',   'Utilisateur'

    email      = models.EmailField(unique=True)
    role       = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    phone      = models.CharField(max_length=20, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name      = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER

    @property
    def is_regular_user(self):
        return self.role == self.Role.USER