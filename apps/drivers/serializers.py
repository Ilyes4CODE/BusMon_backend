from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Absence, AbsenceHistory, DriverProfile


class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = DriverProfile
        fields = ['id', 'user', 'license_number', 'license_expiry',
                  'experience_years', 'is_available', 'created_at']
        read_only_fields = ['id', 'created_at']


class DriverProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DriverProfile
        fields = ['license_number', 'license_expiry', 'experience_years', 'is_available']


class AbsenceSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    type_label  = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model  = Absence
        fields = ['id', 'driver', 'driver_name', 'start_date', 'end_date',
                  'type', 'type_label', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class AbsenceHistorySerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = AbsenceHistory
        fields = [
            'id', 'driver', 'driver_name', 'date', 'status', 'status_label',
            'notes', 'auto_generated', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'auto_generated']
