from django.contrib import admin
from .models import Route, Stop, Trip

class StopInline(admin.TabularInline):
    model  = Stop
    extra  = 1
    fields = ['order', 'name', 'lat', 'lng']

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display  = ['name', 'origin', 'destination', 'distance_km', 'duration_min', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name', 'origin', 'destination']
    inlines       = [StopInline]
    list_editable = ['is_active']

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display  = ['route', 'bus', 'driver', 'departure_time', 'status', 'delay_minutes']
    list_filter   = ['status', 'route']
    search_fields = ['route__name', 'driver__first_name', 'bus__plate_number']
    ordering      = ['-departure_time']
    raw_id_fields = ['bus', 'driver']