from django.contrib import admin
from .models import DriverRating

@admin.register(DriverRating)
class DriverRatingAdmin(admin.ModelAdmin):
    list_display  = ['driver', 'rated_by', 'stars', 'trip', 'created_at']
    list_filter   = ['stars']
    search_fields = ['driver__first_name', 'driver__last_name', 'rated_by__email']
    ordering      = ['-created_at']
    readonly_fields = ['created_at']
    raw_id_fields   = ['driver', 'rated_by', 'trip']