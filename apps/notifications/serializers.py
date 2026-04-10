from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_label       = serializers.CharField(source='get_type_display', read_only=True)
    recipient_email  = serializers.SerializerMethodField()
    is_broadcast     = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = ['id', 'title', 'body', 'type', 'type_label',
                  'is_read', 'recipient', 'recipient_email',
                  'is_broadcast', 'data', 'created_at']
        read_only_fields = ['id', 'created_at', 'type_label',
                            'recipient_email', 'is_broadcast']

    def get_recipient_email(self, obj):
        return obj.recipient.email if obj.recipient else None

    def get_is_broadcast(self, obj):
        return obj.recipient is None