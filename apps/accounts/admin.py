from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering      = ['-created_at']
    fieldsets = (
        (None,            {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Role',          {'fields': ('role',)}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates',         {'fields': ('last_login', 'created_at')}),
    )
    readonly_fields   = ['created_at', 'last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )