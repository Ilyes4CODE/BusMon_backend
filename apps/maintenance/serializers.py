from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
 
from apps.accounts.permissions import IsAdmin, IsAdminOrDriver
from apps.buses.models import Bus
from .models import MaintenanceRecord, Breakdown

 
class MaintenanceRecordSerializer(serializers.ModelSerializer):
    bus_plate = serializers.CharField(source='bus.plate_number', read_only=True)
 
    class Meta:
        model  = MaintenanceRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']
 
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        instance = super().create(validated_data)
        instance.bus.status = Bus.Status.MAINTENANCE
        instance.bus.save(update_fields=['status'])
        return instance
 
 
class BreakdownSerializer(serializers.ModelSerializer):
    bus_plate        = serializers.CharField(source='bus.plate_number', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    status_label     = serializers.CharField(source='get_status_display', read_only=True)
 
    class Meta:
        model  = Breakdown
        fields = '__all__'
        read_only_fields = ['id', 'reported_by', 'reported_at', 'resolved_at',
                            'alert_sent', 'alert_sent_at', 'resolved_by']
 
    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        instance = super().create(validated_data)
        # Auto-set bus to maintenance
        instance.bus.status = Bus.Status.MAINTENANCE
        instance.bus.save(update_fields=['status'])
        return instance
 
 
class SendAlertSerializer(serializers.Serializer):
    """Driver sends alert when breakdown occurs."""
    alert_message = serializers.CharField(required=True, max_length=500)
 
 
class ResolveBreakdownSerializer(serializers.Serializer):
    """Driver/Admin must provide root_cause when resolving."""
    root_cause       = serializers.CharField(required=True)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)