from django.contrib import admin
from .models import DriverProfile, Absence

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'license_number', 'license_expiry', 'experience_years', 'is_available']
    list_filter   = ['is_available']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'license_number']
    list_editable = ['is_available']
    raw_id_fields = ['user']

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display  = ['driver', 'type', 'start_date', 'end_date', 'reason']
    list_filter   = ['type']
    search_fields = ['driver__first_name', 'driver__last_name']
    ordering      = ['-start_date']