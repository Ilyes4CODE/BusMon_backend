from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['title', 'type', 'recipient', 'is_read', 'created_at']
    list_filter   = ['type', 'is_read']
    search_fields = ['title', 'body', 'recipient__email']
    ordering      = ['-created_at']
    readonly_fields = ['created_at']
    list_editable   = ['is_read']
    raw_id_fields   = ['recipient']