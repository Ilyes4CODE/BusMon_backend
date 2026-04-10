from django.contrib import admin
from .models import Bus

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display  = ['plate_number', 'brand', 'model', 'capacity', 'year',
                     'status', 'driver', 'is_active', 'last_location_update']
    list_filter   = ['status', 'brand', 'is_active']
    search_fields = ['plate_number', 'brand', 'model', 'driver__first_name', 'driver__email']
    ordering      = ['plate_number']
    readonly_fields  = ['last_location_update', 'created_at', 'updated_at']
    raw_id_fields    = ['driver']
    list_editable    = ['status', 'is_active']
    fieldsets = (
        ('Bus Info',   {'fields': ('plate_number', 'brand', 'model', 'capacity', 'year', 'is_active', 'notes')}),
        ('Assignment', {'fields': ('driver', 'status')}),
        ('GPS',        {'fields': ('latitude', 'longitude', 'last_location_update')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )