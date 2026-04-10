from django.contrib import admin
from .models import MaintenanceRecord, Breakdown

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display  = ['bus', 'type', 'date', 'cost', 'performed_by', 'next_date', 'created_by']
    list_filter   = ['type', 'date']
    search_fields = ['bus__plate_number', 'description', 'performed_by']
    ordering      = ['-date']
    raw_id_fields = ['bus', 'created_by']

@admin.register(Breakdown)
class BreakdownAdmin(admin.ModelAdmin):
    list_display  = ['bus', 'reported_by', 'status', 'alert_sent', 'reported_at', 'resolved_at']
    list_filter   = ['status', 'alert_sent']
    search_fields = ['bus__plate_number', 'description', 'root_cause']
    ordering      = ['-reported_at']
    readonly_fields = ['reported_at', 'resolved_at', 'alert_sent_at']
    raw_id_fields   = ['bus', 'reported_by', 'resolved_by']
    fieldsets = (
        ('Breakdown Info', {'fields': ('bus', 'reported_by', 'description', 'location_desc', 'latitude', 'longitude', 'status')}),
        ('Alert',          {'fields': ('alert_sent', 'alert_sent_at', 'alert_message')}),
        ('Resolution',     {'fields': ('root_cause', 'resolution_notes', 'resolved_by', 'resolved_at')}),
        ('Timestamps',     {'fields': ('reported_at',)}),
    )